import argparse
import asyncio
import datetime
import glob
import io
import json
import logging
import math
import os
import sys
import uuid
from contextlib import ExitStack
from datetime import datetime as dt
from functools import cached_property
from getpass import getpass
from pathlib import Path
from time import sleep
from typing import BinaryIO, Callable, Dict, List, Union

import folioclient
import httpx
import inquirer
import pymarc
import tabulate
from humps import decamelize
from tqdm import tqdm

from folio_data_import.custom_exceptions import FolioDataImportBatchError, FolioDataImportJobError
from folio_data_import.marc_preprocessors._preprocessors import MARCPreprocessor

try:
    datetime_utc = datetime.UTC
except AttributeError:
    datetime_utc = datetime.timezone.utc


# The order in which the report summary should be displayed
REPORT_SUMMARY_ORDERING = {"created": 0, "updated": 1, "discarded": 2, "error": 3}

# Set default timeout and backoff values for HTTP requests when retrying job status and final summary checks
RETRY_TIMEOUT_START = 5
RETRY_TIMEOUT_RETRY_FACTOR = 1.5
RETRY_TIMEOUT_MAX = 25.32

# Custom log level for data issues, set to 26
DATA_ISSUE_LVL_NUM = 26
logging.addLevelName(DATA_ISSUE_LVL_NUM, "DATA_ISSUES")


def data_issues(self, msg, *args, **kws):
    if self.isEnabledFor(DATA_ISSUE_LVL_NUM):
        self._log(DATA_ISSUE_LVL_NUM, msg, args, **kws)


logging.Logger.data_issues = data_issues

logger = logging.getLogger(__name__)


class MARCImportJob:
    """
    Class to manage importing MARC data (Bib, Authority) into FOLIO using the Change Manager
    APIs (https://github.com/folio-org/mod-source-record-manager/tree/master?tab=readme-ov-file#data-import-workflow),
    rather than file-based Data Import. When executed in an interactive environment, it can provide progress bars
    for tracking the number of records both uploaded and processed.

    Args:
        folio_client (FolioClient): An instance of the FolioClient class.
        marc_files (list): A list of Path objects representing the MARC files to import.
        import_profile_name (str): The name of the data import job profile to use.
        batch_size (int): The number of source records to include in a record batch (default=10).
        batch_delay (float): The number of seconds to wait between record batches (default=0).
        no_progress (bool): Disable progress bars (eg. for running in a CI environment).
    """

    bad_records_file: io.TextIOWrapper
    failed_batches_file: io.TextIOWrapper
    job_id: str
    pbar_sent: tqdm
    pbar_imported: tqdm
    http_client: httpx.Client
    current_file: List[Path]
    record_batch: List[dict] = []
    last_current: int = 0
    total_records_sent: int = 0
    finished: bool = False
    job_id: str = ""
    job_hrid: int = 0
    current_file: Union[List[Path], List[io.BytesIO]] = []
    _max_summary_retries: int = 2
    _max_job_retries: int = 2
    _job_retries: int = 0
    _summary_retries: int = 0

    def __init__(
        self,
        folio_client: folioclient.FolioClient,
        marc_files: List[Path],
        import_profile_name: str,
        batch_size=10,
        batch_delay=0,
        marc_record_preprocessor: Union[List[Callable], str] = [],
        preprocessor_args: Dict[str, Dict] = {},
        no_progress=False,
        let_summary_fail=False,
        split_files=False,
        split_size=1000,
        split_offset=0,
    ) -> None:
        self.split_files = split_files
        self.split_size = split_size
        self.split_offset = split_offset
        self.no_progress = no_progress
        self.let_summary_fail = let_summary_fail
        self.folio_client: folioclient.FolioClient = folio_client
        self.import_files = marc_files
        self.import_profile_name = import_profile_name
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        self.current_retry_timeout = 0
        self.marc_record_preprocessor: MARCPreprocessor = MARCPreprocessor(
            marc_record_preprocessor, **preprocessor_args
        )

    async def do_work(self) -> None:
        """
        Performs the necessary work for data import.

        This method initializes an HTTP client, files to store records that fail to send,
        and calls the appropriate method to import MARC files based on the configuration.

        Returns:
            None
        """
        with (
            httpx.Client() as http_client,
            open(
                self.import_files[0].parent.joinpath(
                    f"bad_marc_records_{dt.now(tz=datetime_utc).strftime('%Y%m%d%H%M%S')}.mrc"
                ),
                "wb+",
            ) as bad_marc_file,
            open(
                self.import_files[0].parent.joinpath(
                    f"failed_batches_{dt.now(tz=datetime_utc).strftime('%Y%m%d%H%M%S')}.mrc"
                ),
                "wb+",
            ) as failed_batches,
        ):
            self.bad_records_file = bad_marc_file
            logger.info(f"Writing bad records to {self.bad_records_file.name}")
            self.failed_batches_file = failed_batches
            logger.info(f"Writing failed batches to {self.failed_batches_file.name}")
            self.http_client = http_client
            if self.split_files:
                await self.process_split_files()
            else:
                for file in self.import_files:
                    self.current_file = [file]
                    await self.import_marc_file()
            await self.wrap_up()

    async def process_split_files(self):
        """
        Process the import of files in smaller batches.
        This method is called when `split_files` is set to True.
        It splits each file into smaller chunks and processes them one by one.
        """
        for file in self.import_files:
            with open(file, "rb") as f:
                file_length = await self.read_total_records([f])
            expected_batches = math.ceil(file_length / self.split_size)
            logger.info(
                f"{file.name} contains {file_length} records. Splitting into {expected_batches} {self.split_size} record batches."
            )
            zero_pad_parts = len(str(expected_batches)) if expected_batches > 1 else 2
            for idx, batch in enumerate(
                self.split_marc_file(file, self.split_size), start=1
            ):
                if idx > self.split_offset:
                    batch.name = f"{file.name} (Part {idx:0{zero_pad_parts}})"
                    self.current_file = [batch]
                    await self.import_marc_file()
            self.move_file_to_complete(file)

    async def wrap_up(self) -> None:
        """
        Wraps up the data import process.

        This method is called after the import process is complete.
        It checks for empty bad records and error files and removes them.

        Returns:
            None
        """
        with open(self.bad_records_file.name, "rb") as bad_records:
            if not bad_records.read(1):
                os.remove(bad_records.name)
                logger.info("No bad records found. Removing bad records file.")
        with open(self.failed_batches_file.name, "rb") as failed_batches:
            if not failed_batches.read(1):
                os.remove(failed_batches.name)
                logger.info("No failed batches. Removing failed batches file.")
        logger.info("Import complete.")
        logger.info(f"Total records imported: {self.total_records_sent}")

    async def get_job_status(self) -> None:
        """
        Retrieves the status of a job execution.

        Returns:
            None

        Raises:
            IndexError: If the job execution with the specified ID is not found.
        """
        try:
            self.current_retry_timeout = (
                (self.current_retry_timeout * RETRY_TIMEOUT_RETRY_FACTOR)
                if self.current_retry_timeout
                else RETRY_TIMEOUT_START
            )
            with httpx.Client(
                timeout=self.current_retry_timeout,
                verify=self.folio_client.ssl_verify,
            ) as temp_client:
                self.folio_client.httpx_client = temp_client
                job_status = self.folio_client.folio_get(
                    "/metadata-provider/jobExecutions?statusNot=DISCARDED&uiStatusAny"
                    "=PREPARING_FOR_PREVIEW&uiStatusAny=READY_FOR_PREVIEW&uiStatusAny=RUNNING&limit=50"
                )
                self.current_retry_timeout = None
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.HTTPStatusError) as e:
            error_text = e.response.text if hasattr(e, "response") else str(e)
            if self.current_retry_timeout <= RETRY_TIMEOUT_MAX and (
                not hasattr(e, "response") or e.response.status_code in [502, 504, 401]
            ):
                logger.warning(
                    f"SERVER ERROR fetching job status: {error_text}. Retrying."
                )
                sleep(0.25)
                return await self.get_job_status()
            elif self.current_retry_timeout > RETRY_TIMEOUT_MAX and (
                not hasattr(e, "response") or e.response.status_code in [502, 504, 401]
            ):
                logger.critical(
                    f"SERVER ERROR fetching job status: {error_text}. Max retries exceeded."
                )
                raise FolioDataImportJobError(self.job_id, error_text, e)
            else:
                raise e
        except Exception as e:
            logger.error(f"Error fetching job status. {e}")

        try:
            status = [
                job for job in job_status["jobExecutions"] if job["id"] == self.job_id
            ][0]
            self.pbar_imported.update(status["progress"]["current"] - self.last_current)
            self.last_current = status["progress"]["current"]
        except (IndexError, ValueError, KeyError):
            logger.debug(
                f"No active job found with ID {self.job_id}. Checking for finished job."
            )
            try:
                job_status = self.folio_client.folio_get(
                    "/metadata-provider/jobExecutions?limit=100&sortBy=completed_date%2Cdesc&statusAny"
                    "=COMMITTED&statusAny=ERROR&statusAny=CANCELLED"
                )
                status = [
                    job
                    for job in job_status["jobExecutions"]
                    if job["id"] == self.job_id
                ][0]
                self.pbar_imported.update(
                    status["progress"]["current"] - self.last_current
                )
                self.last_current = status["progress"]["current"]
                self.finished = True
            except (
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.HTTPStatusError,
            ) as e:
                if not hasattr(e, "response") or e.response.status_code in [502, 504]:
                    error_text = e.response.text if hasattr(e, "response") else str(e)
                    logger.warning(
                        f"SERVER ERROR fetching job status: {error_text}. Retrying."
                    )
                    sleep(0.25)
                    with httpx.Client(
                        timeout=self.current_retry_timeout,
                        verify=self.folio_client.ssl_verify,
                    ) as temp_client:
                        self.folio_client.httpx_client = temp_client
                        return await self.get_job_status()
                else:
                    raise e

    async def create_folio_import_job(self) -> None:
        """
        Creates a job execution for importing data into FOLIO.

        Returns:
            None

        Raises:
            HTTPError: If there is an error creating the job.
        """
        try:
            create_job = self.http_client.post(
                self.folio_client.gateway_url + "/change-manager/jobExecutions",
                headers=self.folio_client.okapi_headers,
                json={"sourceType": "ONLINE", "userId": self.folio_client.current_user},
            )
            create_job.raise_for_status()
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.HTTPStatusError) as e:
            if not hasattr(e, "response") or e.response.status_code in [502, 504]:
                logger.warning(f"SERVER ERROR creating job: {e}. Retrying.")
                sleep(0.25)
                return await self.create_folio_import_job()
            else:
                logger.error(
                    "Error creating job: "
                    + str(e)
                    + "\n"
                    + getattr(getattr(e, "response", ""), "text", "")
                )
                raise e
        self.job_id = create_job.json()["parentJobExecutionId"]
        logger.info(f"Created job: {self.job_id}")

    @cached_property
    def import_profile(self) -> dict:
        """
        Returns the import profile for the current job execution.

        Returns:
            dict: The import profile for the current job execution.
        """
        import_profiles = self.folio_client.folio_get(
            "/data-import-profiles/jobProfiles",
            "jobProfiles",
            query_params={"limit": "1000"},
        )
        profile = [
            profile
            for profile in import_profiles
            if profile["name"] == self.import_profile_name
        ][0]
        return profile

    async def set_job_profile(self) -> None:
        """
        Sets the job profile for the current job execution.

        Returns:
            The response from the HTTP request to set the job profile.
        """
        set_job_profile = self.http_client.put(
            self.folio_client.gateway_url
            + "/change-manager/jobExecutions/"
            + self.job_id
            + "/jobProfile",
            headers=self.folio_client.okapi_headers,
            json={
                "id": self.import_profile["id"],
                "name": self.import_profile["name"],
                "dataType": "MARC",
            },
        )
        try:
            set_job_profile.raise_for_status()
            self.job_hrid = set_job_profile.json()["hrId"]
            logger.info(f"Job HRID: {self.job_hrid}")
        except httpx.HTTPError as e:
            logger.error(
                "Error creating job: "
                + str(e)
                + "\n"
                + getattr(getattr(e, "response", ""), "text", "")
            )
            raise e

    @staticmethod
    async def read_total_records(files: List[BinaryIO]) -> int:
        """
        Reads the total number of records from the given files.

        Args:
            files (list): List of files to read.

        Returns:
            int: The total number of records found in the files.
        """
        total_records = 0
        for import_file in files:
            while True:
                chunk = import_file.read(104857600)
                if not chunk:
                    break
                total_records += chunk.count(b"\x1d")
            import_file.seek(0)
        return total_records

    async def process_record_batch(self, batch_payload) -> None:
        """
        Processes a record batch.

        Args:
            batch_payload (dict): A records payload containing the current batch of MARC records.
        """
        try:
            post_batch = self.http_client.post(
                self.folio_client.gateway_url
                + f"/change-manager/jobExecutions/{self.job_id}/records",
                headers=self.folio_client.okapi_headers,
                json=batch_payload,
            )
        except (httpx.ConnectTimeout, httpx.ReadTimeout):
            logger.warning(
                f"CONNECTION ERROR posting batch {batch_payload['id']}. Retrying..."
            )
            sleep(0.25)
            return await self.process_record_batch(batch_payload)
        try:
            post_batch.raise_for_status()
            self.total_records_sent += len(self.record_batch)
            self.record_batch = []
            self.pbar_sent.update(len(batch_payload["initialRecords"]))
        except httpx.HTTPStatusError as e:
            if (
                e.response.status_code in [500, 400, 422]
            ):  # TODO: Update once we no longer have to support < Sunflower to just be 400
                self.total_records_sent += len(self.record_batch)
                self.record_batch = []
                self.pbar_sent.update(len(batch_payload["initialRecords"]))
            else:
                for record in self.record_batch:
                    self.failed_batches_file.write(record)
                raise FolioDataImportBatchError(
                    batch_payload["id"], f"{e}\n{e.response.text}", e
                )
        await self.get_job_status()
        sleep(self.batch_delay)

    async def process_records(self, files, total_records) -> None:
        """
        Process records from the given files.

        Args:
            files (list): List of files to process.
            total_records (int): Total number of records to process.
            pbar_sent: Progress bar for tracking the number of records sent.

        Returns:
            None
        """
        counter = 0
        for import_file in files:
            file_path = Path(import_file.name)
            self.pbar_sent.set_description(
                f"Sent ({os.path.basename(import_file.name)}): "
            )
            reader = pymarc.MARCReader(import_file, hide_utf8_warnings=True)
            for idx, record in enumerate(reader, start=1):
                if len(self.record_batch) == self.batch_size:
                    await self.process_record_batch(
                        await self.create_batch_payload(
                            counter,
                            total_records,
                            counter == total_records,
                        ),
                    )
                    sleep(0.25)
                if record:
                    record = self.marc_record_preprocessor.do_work(record)
                    self.record_batch.append(record.as_marc())
                    counter += 1
                else:
                    logger.data_issues(
                        "RECORD FAILED\t%s\t%s\t%s",
                        f"{file_path.name}:{idx}",
                        f"Error reading {idx} record from {file_path}. Skipping. Writing current chunk to {self.bad_records_file.name}.",
                        "",
                    )
                    self.bad_records_file.write(reader.current_chunk)
            if not self.split_files:
                self.move_file_to_complete(file_path)
        if self.record_batch or not self.finished:
            await self.process_record_batch(
                await self.create_batch_payload(
                    counter,
                    total_records,
                    counter == total_records,
                ),
            )

    def move_file_to_complete(self, file_path: Path):
        import_complete_path = file_path.parent.joinpath("import_complete")
        if not import_complete_path.exists():
            logger.debug(
                f"Creating import_complete directory: {import_complete_path.absolute()}"
            )
            import_complete_path.mkdir(exist_ok=True)
        logger.debug(f"Moving {file_path} to {import_complete_path.absolute()}")
        file_path.rename(file_path.parent.joinpath("import_complete", file_path.name))

    async def create_batch_payload(self, counter, total_records, is_last) -> dict:
        """
        Create a batch payload for data import.

        Args:
            counter (int): The current counter value.
            total_records (int): The total number of records.
            is_last (bool): Indicates if this is the last batch.

        Returns:
            dict: The batch payload containing the ID, records metadata, and initial records.
        """
        return {
            "id": str(uuid.uuid4()),
            "recordsMetadata": {
                "last": is_last,
                "counter": counter,
                "contentType": "MARC_RAW",
                "total": total_records,
            },
            "initialRecords": [{"record": x.decode()} for x in self.record_batch],
        }

    @staticmethod
    def split_marc_file(file_path, batch_size):
        """Generator to iterate over MARC records in batches, yielding BytesIO objects."""
        with open(file_path, "rb") as f:
            batch = io.BytesIO()
            count = 0

            while True:
                leader = f.read(24)
                if not leader:
                    break  # End of file

                try:
                    record_length = int(leader[:5])  # Extract record length from leader
                except ValueError:
                    raise ValueError("Invalid MARC record length encountered.")

                record_body = f.read(record_length - 24)
                if len(record_body) != record_length - 24:
                    raise ValueError(
                        "Unexpected end of file while reading MARC record."
                    )

                # Verify record terminator
                if record_body[-1:] != b"\x1d":
                    raise ValueError(
                        "MARC record does not end with the expected terminator (0x1D)."
                    )

                # Write the full record to the batch buffer
                batch.write(leader + record_body)
                count += 1

                if count >= batch_size:
                    batch.seek(0)
                    yield batch
                    batch = io.BytesIO()  # Reset buffer
                    count = 0

            # Yield any remaining records
            if count > 0:
                batch.seek(0)
                yield batch

    async def import_marc_file(self) -> None:
        """
        Imports MARC file into the system.

        This method performs the following steps:
        1. Creates a FOLIO import job.
        2. Retrieves the import profile.
        3. Sets the job profile.
        4. Opens the MARC file(s) and reads the total number of records.
        5. Displays progress bars for imported and sent records.
        6. Processes the records and updates the progress bars.
        7. Checks the job status periodically until the import is finished.

        Note: This method assumes that the necessary instance attributes are already set.

        Returns:
            None
        """
        await self.create_folio_import_job()
        await self.set_job_profile()
        with ExitStack() as stack:
            try:
                if isinstance(self.current_file[0], Path):
                    files = [
                        stack.enter_context(open(file, "rb"))
                        for file in self.current_file
                    ]
                elif isinstance(self.current_file[0], io.BytesIO):
                    files = [stack.enter_context(file) for file in self.current_file]
                else:
                    raise ValueError("Invalid file type. Must be Path or BytesIO.")
            except IndexError as e:
                logger.error(f"Error opening file: {e}")
                raise e
            total_records = await self.read_total_records(files)
            with (
                tqdm(
                    desc=f"Imported ({self.job_hrid}): ",
                    total=total_records,
                    position=1,
                    disable=self.no_progress,
                ) as pbar_imported,
                tqdm(
                    desc="Sent: ()",
                    total=total_records,
                    position=0,
                    disable=self.no_progress,
                ) as pbar_sent,
            ):
                try:
                    self.pbar_sent = pbar_sent
                    self.pbar_imported = pbar_imported
                    await self.process_records(files, total_records)
                    while not self.finished:
                        await self.get_job_status()
                    await asyncio.sleep(5)
                except FolioDataImportBatchError as e:
                    logger.error(
                        f"Unhandled error posting batch {e.batch_id}: {e.message}"
                    )
                    await self.cancel_job()
                    raise e
                except FolioDataImportJobError as e:
                    await self.cancel_job()
                    if self._job_retries < self._max_job_retries:
                        self._job_retries += 1
                        logger.error(
                            f"Unhandled error processing job {e.job_id}: {e.message}, cancelling and retrying."
                        )
                        await self.import_marc_file()
                    else:
                        logger.critical(
                            f"Unhandled error processing job {e.job_id}: {e.message}, cancelling and exiting (maximum retries reached)."
                        )
                        raise e
            if self.finished:
                await self.log_job_summary()
            self.last_current = 0
            self.finished = False

    async def cancel_job(self) -> None:
        """
        Cancels the current job execution.

        This method sends a request to cancel the job execution and logs the result.

        Returns:
            None
        """
        try:
            cancel = self.http_client.delete(
                self.folio_client.gateway_url
                + f"/change-manager/jobExecutions/{self.job_id}/records",
                headers=self.folio_client.okapi_headers,
            )
            cancel.raise_for_status()
            self.finished = True
            logger.info(f"Cancelled job: {self.job_id}")
        except (httpx.ConnectTimeout, httpx.ReadTimeout):
            logger.warning(
                f"CONNECTION ERROR cancelling job {self.job_id}. Retrying..."
            )
            sleep(0.25)
            await self.cancel_job()

    async def log_job_summary(self):
        if job_summary := await self.get_job_summary():
            job_id = job_summary.pop("jobExecutionId", None)
            total_errors = job_summary.pop("totalErrors", 0)
            columns = ["Summary"] + list(job_summary.keys())
            rows = set()
            for key in columns[1:]:
                rows.update(job_summary[key].keys())

            table_data = []
            for row in rows:
                metric_name = decamelize(row).split("_")[1]
                table_row = [metric_name]
                for col in columns[1:]:
                    table_row.append(job_summary[col].get(row, "N/A"))
                table_data.append(table_row)
            table_data.sort(key=lambda x: REPORT_SUMMARY_ORDERING.get(x[0], 99))
            columns = columns[:1] + [
                " ".join(decamelize(x).split("_")[:-1]) for x in columns[1:]
            ]
            logger.info(
                f"Results for {'file' if len(self.current_file) == 1 else 'files'}: "
                f"{', '.join([os.path.basename(x.name) for x in self.current_file])}"
            )
            logger.info(
                "\n"
                + tabulate.tabulate(table_data, headers=columns, tablefmt="fancy_grid"),
            )
            if total_errors:
                logger.info(f"Total errors: {total_errors}. Job ID: {job_id}.")
        else:
            logger.error(
                f"No job summary available for job #{self.job_hrid}({self.job_id})."
            )

    async def get_job_summary(self) -> dict:
        """
        Retrieves the job summary for the current job execution.

        Returns:
            dict: The job summary for the current job execution.
        """
        try:
            self.current_retry_timeout = (
                (self.current_retry_timeout * RETRY_TIMEOUT_RETRY_FACTOR)
                if self.current_retry_timeout
                else RETRY_TIMEOUT_START
            )
            with httpx.Client(
                timeout=self.current_retry_timeout, verify=self.folio_client.ssl_verify
            ) as temp_client:
                self.folio_client.httpx_client = temp_client
                job_summary = self.folio_client.folio_get(
                    f"/metadata-provider/jobSummary/{self.job_id}"
                )
            self.current_retry_timeout = None
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.HTTPStatusError) as e:
            error_text = e.response.text if hasattr(e, "response") else str(e)
            if (self._max_summary_retries > self._summary_retries) and (
                not hasattr(e, "response")
                or (hasattr(e, "response") and e.response.status_code in [502, 504])
                and not self.let_summary_fail
            ):
                logger.warning(f"SERVER ERROR fetching job summary: {e}. Retrying.")
                sleep(0.25)
                with httpx.Client(
                    timeout=self.current_retry_timeout,
                    verify=self.folio_client.ssl_verify,
                ) as temp_client:
                    self.folio_client.httpx_client = temp_client
                    self._summary_retries += 1
                    return await self.get_job_summary()
            elif (self._summary_retries >= self._max_summary_retries) or (
                hasattr(e, "response")
                and (e.response.status_code in [502, 504] and self.let_summary_fail)
            ):
                logger.warning(
                    f"SERVER ERROR fetching job summary: {error_text}. Skipping final summary check."
                )
                job_summary = {}
            else:
                raise e
        return job_summary


def set_up_cli_logging():
    """
    This function sets up logging for the CLI.
    """
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Set up file and stream handlers
    file_handler = logging.FileHandler(
        "folio_data_import_{}.log".format(dt.now().strftime("%Y%m%d%H%M%S"))
    )
    file_handler.setLevel(logging.INFO)
    file_handler.addFilter(ExcludeLevelFilter(DATA_ISSUE_LVL_NUM))
    # file_handler.addFilter(IncludeLevelFilter(25))
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    if not any(
        isinstance(h, logging.StreamHandler) and h.stream == sys.stderr
        for h in logger.handlers
    ):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.addFilter(ExcludeLevelFilter(DATA_ISSUE_LVL_NUM))
        # stream_handler.addFilter(ExcludeLevelFilter(25))
        stream_formatter = logging.Formatter("%(message)s")
        stream_handler.setFormatter(stream_formatter)
        logger.addHandler(stream_handler)

    # Set up data issues logging
    data_issues_handler = logging.FileHandler(
        "marc_import_data_issues_{}.log".format(dt.now().strftime("%Y%m%d%H%M%S"))
    )
    data_issues_handler.setLevel(26)
    data_issues_handler.addFilter(IncludeLevelFilter(DATA_ISSUE_LVL_NUM))
    data_issues_formatter = logging.Formatter("%(message)s")
    data_issues_handler.setFormatter(data_issues_formatter)
    logger.addHandler(data_issues_handler)

    # Stop httpx from logging info messages to the console
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def main() -> None:
    """
    Main function to run the MARC import job.

    This function parses command line arguments, initializes the FolioClient,
    and runs the MARCImportJob.
    """
    set_up_cli_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway_url", type=str, help="The FOLIO API Gateway URL")
    parser.add_argument("--tenant_id", type=str, help="The FOLIO tenant ID")
    parser.add_argument(
        "--member_tenant_id",
        type=str,
        help="The FOLIO ECS member tenant ID (if applicable)",
        default="",
    )
    parser.add_argument("--username", type=str, help="The FOLIO username")
    parser.add_argument("--password", type=str, help="The FOLIO password", default="")
    parser.add_argument(
        "--marc_file_path",
        type=str,
        help="The MARC file (or file glob, using shell globbing syntax) to import",
    )
    parser.add_argument(
        "--import_profile_name",
        type=str,
        help="The name of the data import job profile to use",
        default="",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        help="The number of source records to include in a record batch sent to FOLIO.",
        default=10,
    )
    parser.add_argument(
        "--batch_delay",
        type=float,
        help="The number of seconds to wait between record batches.",
        default=0.0,
    )
    parser.add_argument(
        "--preprocessor",
        type=str,
        help=(
            "Comma-separated python import paths to Python function(s) "
            "to apply to each MARC record before sending to FOLIO. Function should take "
            "a pymarc.Record object as input and return a pymarc.Record object."
        ),
        default="",
    )

    parser.add_argument(
        "--split-files",
        action="store_true",
        help="Split files into smaller parts before importing.",
    )
    parser.add_argument(
        "--split-size",
        type=int,
        help="The number of records to include in each split file.",
        default=1000,
    )
    parser.add_argument(
        "--split-offset",
        type=int,
        help="The number of record batches of <split-size> to skip before starting import.",
        default=0,
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars (eg. for running in a CI environment)",
    )
    parser.add_argument(
        "--let-summary-fail",
        action="store_true",
        help="Do not retry fetching the final job summary if it fails",
    )
    parser.add_argument(
        "--preprocessor-config",
        type=str,
        help=(
            "JSON file containing configuration for preprocessor functions. "
            "This is passed to MARCPreprocessor class as a dict of dicts."
        ),
        default=None,
    )

    args = parser.parse_args()
    if not args.password:
        args.password = getpass("Enter FOLIO password: ")
    folio_client = folioclient.FolioClient(
        args.gateway_url, args.tenant_id, args.username, args.password
    )

    # Set the member tenant id if provided to support FOLIO ECS multi-tenant environments
    if args.member_tenant_id:
        folio_client.okapi_headers["x-okapi-tenant"] = args.member_tenant_id

    if os.path.isabs(args.marc_file_path):
        marc_files = [Path(x) for x in glob.glob(args.marc_file_path)]
    else:
        marc_files = list(Path("./").glob(args.marc_file_path))

    marc_files.sort()

    if len(marc_files) == 0:
        logger.critical(f"No files found matching {args.marc_file_path}. Exiting.")
        sys.exit(1)
    else:
        logger.info(marc_files)

    if args.preprocessor_config:
        with open(args.preprocessor_config, "r") as f:
            preprocessor_args = json.load(f)
    else:
        preprocessor_args = {}

    if not args.import_profile_name:
        import_profiles = folio_client.folio_get(
            "/data-import-profiles/jobProfiles",
            "jobProfiles",
            query_params={"limit": "1000"},
        )
        import_profile_names = [
            profile["name"]
            for profile in import_profiles
            if "marc" in profile["dataType"].lower()
        ]
        questions = [
            inquirer.List(
                "import_profile_name",
                message="Select an import profile",
                choices=import_profile_names,
            )
        ]
        answers = inquirer.prompt(questions)
        args.import_profile_name = answers["import_profile_name"]
    try:
        await MARCImportJob(
            folio_client,
            marc_files,
            args.import_profile_name,
            batch_size=args.batch_size,
            batch_delay=args.batch_delay,
            marc_record_preprocessor=args.preprocessor,
            preprocessor_args=preprocessor_args,
            no_progress=bool(args.no_progress),
            let_summary_fail=bool(args.let_summary_fail),
            split_files=bool(args.split_files),
            split_size=args.split_size,
            split_offset=args.split_offset,
        ).do_work()
    except Exception as e:
        logger.error("Error importing files: " + str(e))
        raise


class ExcludeLevelFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno != self.level


class IncludeLevelFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno == self.level


def sync_main() -> None:
    """
    Synchronous main function to run the MARC import job.
    """
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
