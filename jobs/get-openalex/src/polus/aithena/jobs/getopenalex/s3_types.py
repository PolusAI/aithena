# mypy: disable-error-code="import-untyped"
"""Db for OpenAlex types."""
# pylint: disable=W1203, E1101, E0401
import logging
from datetime import date as Date
from pathlib import Path
from typing import Any, Literal, Optional, Union

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from polus.aithena.common.logger import get_logger
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator
from pydantic.dataclasses import dataclass
from tqdm import tqdm

logger = get_logger(__file__)

TYPES = ["works", "authors", "topics", "concepts",
         "institutions", "publishers", "sources"]


# --- S3 ---
class S3Directory(BaseModel):
    """Pydantic Model to Represent S3 Directory from OpenAlex Snapshot.

    Internally initialized from the `ls` method of `SnapshotS3`.
    Not meant to be used directly, but as a helper for `SnapshotS3`.
    """
    Prefix: str = Field(..., alias=AliasChoices(  # type: ignore
        "prefix", "name", "Prefix"))
    type: Literal["works", "authors", "topics", "concepts",
                  "institutions", "publishers", "sources"]
    date: Date

    @model_validator(mode="before")
    def _from_prefix(self):
        if not self["Prefix"].startswith("data/"):
            raise ValueError(
                f"Prefix must start with 'data/': {self['Prefix']}")
        parts = self["Prefix"].split("/")
        if len(parts) != 4:
            raise ValueError(f"Prefix must have 3 parts: {self['Prefix']}")
        self["type"] = parts[1]
        self["date"] = parts[2].split("=")[1]
        return self

    def __gt__(self, other: Union["S3Directory", Date, str]):
        if isinstance(other, Date):
            return self.date > other
        if isinstance(other, str):
            return self.date > Date.fromisoformat(other)
        if isinstance(other, S3Directory):
            return self.date > other.date
        raise ValueError("other must be of type S3Directory, date, or str")

    def __lt__(self, other: Union["S3Directory", Date, str]):
        if isinstance(other, Date):
            return self.date < other
        if isinstance(other, str):
            return self.date < Date.fromisoformat(other)
        if isinstance(other, S3Directory):
            return self.date < other.date
        raise ValueError("other must be of type S3Directory, date, or str")

    def __ge__(self, other: Union["S3Directory", Date, str]):
        if isinstance(other, Date):
            return self.date >= other
        if isinstance(other, str):
            return self.date >= Date.fromisoformat(other)
        if isinstance(other, S3Directory):
            return self.date >= other.date
        raise ValueError("other must be of type S3Directory, date, or str")

    def __le__(self, other: Union["S3Directory", Date, str]):
        if isinstance(other, Date):
            return self.date <= other
        if isinstance(other, str):
            return self.date <= Date.fromisoformat(other)
        if isinstance(other, S3Directory):
            return self.date <= other.date
        raise ValueError("other must be of type S3Directory, date, or str.")


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class SnapshotS3:
    """Interface to interact with OpenAlex snapshot on S3."""
    s3: boto3.session.Session = Field(default_factory=lambda: boto3.client(
        's3', config=Config(signature_version=UNSIGNED)), frozen=True)
    bucket_name: str = Field(default="openalex", frozen=True)

    def ls(self, prefix: Optional[str] = None,
           delimiter: Optional[str] = None, names: bool = False, **kwargs) -> Any:
        """List objects in S3 bucket.

        If `names=True`, return only the names of the objects (files-dirs).
        """
        if prefix is not None:
            kwargs["Prefix"] = prefix
        if delimiter is not None:
            kwargs["Delimiter"] = delimiter
        response = self.s3.list_objects_v2(Bucket=self.bucket_name, **kwargs)
        if "Contents" not in response and names:
            logger.warning(
                f"Did not return any contents: {kwargs}, names={names}")
            return response
        if names:
            return [obj["Key"] for obj in response["Contents"]]
        return response

    def ls_dirs(self, type_: str,
                from_date: str | Date | None = None, **kwargs) -> list[S3Directory]:
        """List directories in S3 bucket."""
        logger.debug(f"Listing directories for {type_}, from_date={from_date}")
        res = self.ls(prefix=f"data/{type_}/",
                      delimiter="/", **kwargs)
        cp = res.get("CommonPrefixes", [])
        if cp == []:
            logger.error(f"Failed to list directories for {type_}")
            logger.debug(f"Response: {res}")
            raise ValueError(f"Failed to list directories for {type_}")
        ls = [S3Directory(**dir) for dir in cp]
        logger.debug(
            f"Found {len(ls)} directories for {type_} before filtering")
        if from_date is not None:
            return [d for d in ls if d >= from_date]
        return ls

    def ls_dirs_dict(self, from_date: str | Date | None = None,
                     **kwargs) -> dict[str, list[S3Directory]]:
        """List directories in S3 bucket as a dictionary."""
        res = {}
        for tp in TYPES:
            res[tp] = self.ls_dirs(tp, from_date=from_date, **kwargs)
        return res

    def download_dir(self, name: S3Directory, output_path: str | Path,
                     return_list: bool = False) -> Any:
        """Download directory from S3 - Recursive.

        If `return_list=True`, return a list of `SnapshotGZ` to the downloaded files.
        """
        outdir = Path(output_path)
        files_ = self.ls(prefix=name.Prefix, names=True)
        logger.info(f"Downloading {name.Prefix} to {outdir.absolute()}")
        logger.debug(f"Found: {files_}")
        out_ = outdir.joinpath(name.Prefix.split('/')[-2])
        out_.mkdir(parents=True, exist_ok=True)
        if return_list:
            path_list = []
        try:
            for file in tqdm(files_):
                path_ = out_/file.split('/')[-1]
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

    def download_all_of_type(self, type_: str, output_path: str | Path,
                             from_date: str | Date | None = None, return_list: bool = False) -> Any:
        """Download all files of a specific OpenAlex type from S3 - Recursively."""
        dirs = self.ls_dirs(type_, from_date=from_date)
        logger.info(
            f"Downloading {type_} to {output_path}, found {len(dirs)} directories")
        out_dir_full = Path(output_path).joinpath(
            type_)
        out_dir_full.mkdir(parents=True, exist_ok=True)
        if return_list:
            path_list = []
        for dir_ in tqdm(dirs):
            if return_list:
                path_list.extend(self.download_dir(
                    dir_, out_dir_full, return_list=True))
            else:
                self.download_dir(dir_, out_dir_full)
        if return_list:
            return path_list
        return output_path

    def download_all(self, output_path: str | Path,
                     from_date: str | Date | None = None, return_list: bool = False) -> Any:
        """Download all files from S3 - Recursively."""
        res = {}
        for tp in TYPES:
            res[tp] = self.download_all_of_type(
                tp, output_path, from_date=from_date, return_list=return_list)
        if return_list:
            return res
        return output_path
