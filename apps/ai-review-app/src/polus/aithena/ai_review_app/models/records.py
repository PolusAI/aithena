"""Record functions and components for AI Review Dashboard."""

# pylint: disable=W1203, W0106
import re
from typing import Any, Callable

import numpy as np
import pandas as pd
import solara

from qdrant_client.http.models.models import Record

from ..utils.common import get_logger
from ..components.plot import PointSelection
from ..components.database import db
from .. import config


logger = get_logger(__file__)

def get_valid_collections(collections: list[str]):
    """Return a list of valid collections."""
    return collections

def get_default_collection(collections: list[str]):
    """Return a collection according to the default configuration."""
    if config.DEFAULT_COLLECTION and config.DEFAULT_COLLECTION in collections:
        logger.info(f"default collection: {config.DEFAULT_COLLECTION}")
        return config.DEFAULT_COLLECTION
    logger.info(f"select first collection : {collections[0]}")
    return collections[0]

def get_records(collection: str) -> list[Record]:
    """Retrieve records for a given collection."""
    logger.info(f"##### retrieve records for collection {collection}...")
    return db.get_all_records(collection)