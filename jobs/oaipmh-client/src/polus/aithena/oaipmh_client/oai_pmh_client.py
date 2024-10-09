"""OAI-PMH Client."""

import io
import time
from pathlib import Path
from typing import Any
from typing import Optional
from urllib.parse import urlparse

from polus.aithena.oaipmh_client.config import RETRY_ATTEMPTS, TIMEOUT, RETRY_AFTER
import requests
from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import init_dir
from pydantic import BaseModel
from xsdata_pydantic.bindings import XmlParser
from xsdata_pydantic.bindings import XmlSerializer

from . import oai_pmh_types as oai

logger = get_logger(__file__)

HTTP_STATUS_503 = 503
HTTP_STATUS_200 = 200


class OaiPmhClient:
    """OAI-PMH Client."""

    class Options(BaseModel):
        """Base options."""

        verb: oai.VerbType

    class ListRecordsOptions(Options):
        """Batch methods options."""

        metadata_prefix: str | None = None
        from_: oai.XmlDate | None = None
        resumption_token: oai.ResumptionTokenType | None = None

    def __init__(
        self,
        base_url: str,
        out_dir: Path,
        retry_after: int = RETRY_AFTER,
        max_retry: int = RETRY_ATTEMPTS,
    ) -> None:
        """OAI-PMH Client."""
        self.repository_id = urlparse(base_url).netloc
        self.base_url = base_url
        self.parser = XmlParser()
        self.serializer = XmlSerializer()
        self.out_dir = out_dir
        self.downloads_dir = init_dir(out_dir / "downloads")
        self.debug_dir = init_dir(out_dir / "debug")
        self.retry_after = retry_after
        self.max_retry = max_retry

    def build_url(self, options: Options) -> str:
        """Build url for a given method."""
        url = self.base_url
        url = url + f"?verb={options.verb.value}"
        if isinstance(options, OaiPmhClient.ListRecordsOptions):
            if options.metadata_prefix:
                url = url + f"&metadataPrefix={options.metadata_prefix}"
            if options.from_:
                url = url + f"&from={options.from_}"
            if options.resumption_token:
                url = url + f"&resumptionToken={options.resumption_token.value}"
        return url

    def _save_response(self, options: Options, resp: requests.Response) -> None:
        """Save Raw Response to disk."""
        debug_dir = self.debug_dir / options.verb.value
        debug_dir.mkdir(exist_ok=True)
        log_file = debug_dir / f"{options.verb.value}_.xml"
        with log_file.open("wb") as fw:
            fw.write(resp.content)

    def _get(
        self,
        options: Options,
        save: bool = True,
    ) -> tuple[bytes, oai.OaiPmhtype]:
        """Get request with 503 status code management."""
        url = self.build_url(options)
        logger.info(f"rest api call : {url}")
        for retry in list(range(1, self.max_retry + 1)):
            resp = requests.get(url, timeout=TIMEOUT)
            if resp.status_code == HTTP_STATUS_503:
                retry_after = int(resp.headers.get("Retry-After", self.retry_after))
                self.retry_after = retry_after
                logger.info(
                    f"Received 503. Throttling requests. Retry ({retry}) for {url} in {retry_after} seconds.",  # noqa
                )
                time.sleep(retry_after)
            elif resp.status_code == HTTP_STATUS_200:
                logger.info(f"200 response received : {url}")
                if save:
                    self._save_response(options, resp)
                parsed = self.parser.parse(io.BytesIO(resp.content), oai.OaiPmhtype)
                if parsed.error:
                    raise Exception(parsed.error)
                return resp.content, parsed
            else:
                raise Exception(resp)

        msg = "max number of attempts reached..."
        raise Exception(msg)

    def list_metadata_formats(self) -> oai.MetadataFormatType | Any:
        """List Metadata Formats."""
        options = OaiPmhClient.Options(verb=oai.VerbType.LIST_METADATA_FORMATS)
        _, res = self._get(options)
        if res.list_metadata_formats:
            return res.list_metadata_formats.metadata_format
        return None

    def identify(self) -> oai.IdentifyType | None:
        """Identify."""
        options = OaiPmhClient.Options(verb=oai.VerbType.IDENTIFY)
        _, res = self._get(options)
        return res.identify

    def list_records(
        self,
        metadata_prefix: str,
        from_: Optional[oai.XmlDate] = None,
    ) -> None:
        """List Records.

        Incomplete list management with resumption token.
        """
        options = OaiPmhClient.ListRecordsOptions(
            verb=oai.VerbType.LIST_RECORDS,
            metadata_prefix=metadata_prefix,
            from_=from_,
        )

        from_date = str(from_.to_date()) if from_ else "ALL"
        out_dir = (
            self.downloads_dir
            / self.repository_id
            / options.verb.value
            / from_date
            / metadata_prefix
        )
        out_dir.mkdir(exist_ok=True, parents=True)
        batch_index = 0

        while True:
            raw, parsed = self._get(options, save=True)
            records = parsed.list_records
            if records:
                token = records.resumption_token

            if token is not None:
                start_index = token.cursor
                if not token.value.strip():
                    end_index = token.complete_list_size
                else:
                    end_index = int(token.value.split("|")[1]) - 1
                records_file = (
                    out_dir
                    / f"{self.repository_id}_{options.verb.value}_{from_date}_{metadata_prefix}_{start_index}_{end_index}.xml"  # noqa
                )
            else:
                records_file = (out_dir / f"{metadata_prefix}.xml").resolve()
            with records_file.open("wb") as fw:
                logger.info(f"writing response to {records_file}")
                fw.write(raw)
            # if we decide to save the parsed data instead.
            # with open(records_file, "w", encoding="utf-8") as fw:

            # options for next batch
            options = OaiPmhClient.ListRecordsOptions(
                verb=options.verb,
                resumption_token=token,
            )

            batch_index += 1

            if not token or not token.value.strip():
                logger.info("done processing records.")
                break

            logger.debug(f"throttling request every ({self.retry_after}s)...")
            time.sleep(self.retry_after)
