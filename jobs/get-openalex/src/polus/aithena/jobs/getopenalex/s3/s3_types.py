# mypy: disable-error-code="import-untyped"
"""Types for the OpenAlex S3 interface."""
# pylint: disable=W1203, E0401, E0611
from datetime import date
from pathlib import Path
from typing import Any
from typing import Literal
from typing import Union

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pydantic import AliasChoices
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator
from pydantic.dataclasses import dataclass
from tqdm import tqdm

from polus.aithena.jobs.getopenalex.logger import get_logger

logger = get_logger(__file__)

S3_PREFIX_PARTS_EXPECTED = 4  # Expected number of parts in S3 prefix

TYPES = [
    "works",
    "authors",
    "topics",
    "concepts",
    "institutions",
    "publishers",
    "sources",
]


# --- S3 ---
class S3Directory(BaseModel):
    """Pydantic Model to Represent S3 Directory from OpenAlex Snapshot.

    Internally initialized from the `ls` method of `SnapshotS3`.
    Not meant to be used directly, but as a helper for `SnapshotS3`.
    """

    Prefix: str = Field(
        ...,
        alias=AliasChoices("prefix", "name", "Prefix"),  # type: ignore
    )
    type: Literal[
        "works",
        "authors",
        "topics",
        "concepts",
        "institutions",
        "publishers",
        "sources",
    ]
    date: date

    @model_validator(mode="before")
    def _from_prefix(cls, values: dict[str, Any]) -> dict[str, Any]:  # noqa
        """Extract type and date from S3 prefix."""
        prefix = values.get("Prefix")
        if not prefix or not prefix.startswith("data/"):
            raise ValueError(f"Prefix must start with 'data/': {prefix}")
        parts = prefix.split("/")
        if len(parts) != S3_PREFIX_PARTS_EXPECTED:
            raise ValueError(
                f"Prefix must have {S3_PREFIX_PARTS_EXPECTED - 1} parts after 'data/': "
                f"{prefix}",
            )
        values["type"] = parts[1]
        values["date"] = parts[2].split("=")[1]
        return values

    def __gt__(self, other: Union["S3Directory", date, str]) -> bool:
        """Greater than comparison based on date."""
        if isinstance(other, date):
            return self.date > other
        if isinstance(other, str):
            return self.date > date.fromisoformat(other)
        if isinstance(other, S3Directory):
            return self.date > other.date
        raise TypeError(
            f"Unsupported comparison between S3Directory and {type(other).__name__}",
        )

    def __lt__(self, other: Union["S3Directory", date, str]) -> bool:
        """Less than comparison based on date."""
        if isinstance(other, date):
            return self.date < other
        if isinstance(other, str):
            return self.date < date.fromisoformat(other)
        if isinstance(other, S3Directory):
            return self.date < other.date
        raise TypeError(
            f"Unsupported comparison between S3Directory and {type(other).__name__}",
        )

    def __ge__(self, other: Union["S3Directory", date, str]) -> bool:
        """Greater than or equal comparison based on date."""
        if isinstance(other, date):
            return self.date >= other
        if isinstance(other, str):
            return self.date >= date.fromisoformat(other)
        if isinstance(other, S3Directory):
            return self.date >= other.date
        raise TypeError(
            f"Unsupported comparison between S3Directory and {type(other).__name__}",
        )

    def __le__(self, other: Union["S3Directory", date, str]) -> bool:
        """Less than or equal comparison based on date."""
        if isinstance(other, date):
            return self.date <= other
        if isinstance(other, str):
            return self.date <= date.fromisoformat(other)
        if isinstance(other, S3Directory):
            return self.date <= other.date
        raise TypeError(
            f"Unsupported comparison between S3Directory and {type(other).__name__}",
        )


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class SnapshotS3:
    """Interface to interact with OpenAlex snapshot on S3."""

    s3: boto3.session.Session = Field(
        default_factory=lambda: boto3.client(
            "s3",
            config=Config(signature_version=UNSIGNED),
        ),
        frozen=True,
    )
    bucket_name: str = Field(default="openalex", frozen=True)

    def ls(
        self,
        prefix: str | None = None,
        delimiter: str | None = None,
        names: bool = False,
        **kwargs: dict[str, Any],
    ) -> dict[str, Any] | list[str]:
        """List objects in S3 bucket.

        Args:
            prefix: Prefix to list objects from.
            delimiter: Delimiter to list objects from.
            names: If True, return only the names of the objects (files-dirs).
            **kwargs: Additional arguments to pass to the S3 API.

        Returns:
            dict[str, Any] | list[str]: Response from the S3 API.
        """
        if prefix is not None:
            kwargs["Prefix"] = prefix
        if delimiter is not None:
            kwargs["Delimiter"] = delimiter
        response = self.s3.list_objects_v2(Bucket=self.bucket_name, **kwargs)
        if "Contents" not in response and names:
            logger.warning(f"Did not return any contents: {kwargs}, names={names}")
            return response  # Return original response if no contents and names=True
        if names:
            # Ensure 'Contents' exists before list comprehension
            return [obj["Key"] for obj in response.get("Contents", [])]
        return response

    def ls_dirs(
        self,
        type_: str,
        from_date: str | date | None = None,
        **kwargs: dict[str, Any],
    ) -> list[S3Directory]:
        """List directories in S3 bucket.

        Args:
            type_: Type of data to list directories for.
            from_date: Date to list directories from (inclusive).
            **kwargs: Additional arguments to pass to the S3 API.
        """
        logger.debug(f"Listing directories for {type_}, from_date={from_date}")
        res = self.ls(prefix=f"data/{type_}/", delimiter="/", **kwargs)
        cp = res.get("CommonPrefixes", [])
        if cp == []:
            logger.error(f"Failed to list directories for {type_}")
            logger.debug(f"Response: {res}")
            raise ValueError(f"Failed to list directories for {type_}")
        s3_dirs = [S3Directory(**common_prefix) for common_prefix in cp]
        logger.debug(f"Found {len(s3_dirs)} directories for {type_} before filtering")
        if from_date is not None:
            return [d for d in s3_dirs if d >= from_date]
        return s3_dirs

    def ls_dirs_dict(
        self,
        from_date: str | date | None = None,
        **kwargs: dict[str, Any],
    ) -> dict[str, list[S3Directory]]:
        """List directories in S3 bucket as a dictionary.

        Args:
            from_date: Date to list directories from (inclusive).
            **kwargs: Additional arguments to pass to the S3 API.

        Returns:
            dict[str, list[S3Directory]]: Dictionary of types and their directories.
        """
        result_dict = {}
        for tp in TYPES:
            result_dict[tp] = self.ls_dirs(tp, from_date=from_date, **kwargs)
        return result_dict

    def download_dir(
        self,
        name: S3Directory,
        output_path: str | Path,
        return_list: bool = False,
    ) -> Path | list[Path]:
        """Download directory from S3 - Recursive.

        Args:
            name: S3Directory to download.
            output_path: Path to download the directory to.
            return_list: If True, return a list of Paths to the downloaded files.

        Returns:
            Path | list[Path]: Path to the downloaded directory or list of paths.
        """
        outdir = Path(output_path)
        files_ = self.ls(prefix=name.Prefix, names=True)
        logger.info(f"Downloading {name.Prefix} to {outdir.absolute()}")
        logger.debug(f"Found: {files_}")
        out_ = outdir.joinpath(name.Prefix.split("/")[-2])
        out_.mkdir(parents=True, exist_ok=True)
        if return_list:
            path_list = []
        try:
            for file in tqdm(files_):
                path_ = out_ / file.split("/")[-1]
                self.s3.download_file(self.bucket_name, file, path_)
                logger.debug(f"Downloaded {file} to {path_.absolute()}")
                if return_list:
                    path_list.append(path_.absolute())
        except Exception as e:
            logger.error(f"Failed to download {name}: {e}")
            raise e
        logger.debug(f"Downloaded {name} to {outdir.absolute()}")
        if return_list:
            return path_list
        return out_

    def download_all_of_type(
        self,
        type_: str,
        output_path: str | Path,
        from_date: str | date | None = None,
        return_list: bool = False,
    ) -> Path | list[Path]:
        """Download all files of a specific OpenAlex type from S3 - Recursively.

        Args:
            type_: Type of data to download.
            output_path: Path to download the data to.
            from_date: Date to download data from (inclusive).
            return_list: If True, return a list of Paths to the downloaded files.
        """
        s3_dirs = self.ls_dirs(type_, from_date=from_date)
        logger.info(
            f"Downloading {type_} to {output_path}, found {len(s3_dirs)} directories",
        )
        out_dir_full = Path(output_path).joinpath(type_)
        out_dir_full.mkdir(parents=True, exist_ok=True)
        if return_list:
            path_list = []
        for s3_dir in tqdm(s3_dirs):
            if return_list:
                downloaded = self.download_dir(s3_dir, out_dir_full, return_list=True)
                if isinstance(downloaded, list):  # Ensure it's a list before extending
                    path_list.extend(downloaded)
            else:
                self.download_dir(s3_dir, out_dir_full)
        if return_list:
            return path_list
        return output_path

    def download_all(
        self,
        output_path: str | Path,
        from_date: str | date | None = None,
        return_list: bool = False,
    ) -> Path | dict[str, list[Path]]:
        """Download all files from S3 - Recursively.

        Args:
            output_path: Path to download the data to.
            from_date: Date to download data from (inclusive).
            return_list: If True, return a list of Paths to the downloaded files.
        """
        result_data: dict[str, list[Path]] = {}
        for tp in TYPES:
            downloaded = self.download_all_of_type(
                tp,
                output_path,
                from_date=from_date,
                return_list=return_list,
            )
            if return_list and isinstance(downloaded, list):
                result_data[tp] = downloaded
        if return_list:
            return result_data
        return Path(output_path)
