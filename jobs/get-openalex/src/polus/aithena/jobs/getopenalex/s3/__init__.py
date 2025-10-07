"""S3 interface for the OpenAlex REST API."""

from .__main__ import app
from .s3_types import S3Directory
from .s3_types import SnapshotS3

__all__ = ["S3Directory", "SnapshotS3", "app"]
