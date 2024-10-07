"""Utility functions for Aithena."""

from itertools import islice
from pathlib import Path
from typing import Iterable, Iterator, TypeVar
import time
from .logger import exec_time_logger

T = TypeVar('T')

def batcher(iterable : Iterable[T] , batch_size) -> Iterator[T]:
    """Batch an iterable into chunks of size batch_size."""
    iterator = iter(iterable)
    while batch := list(islice(iterator, batch_size)):
        yield batch

def init_dir(dir : Path) -> Path:
    """Create a directory and returns the resolved path."""
    dir = dir.resolve()
    dir.mkdir(exist_ok=True, parents=False)
    return dir

def time_logger(func):
    """Decorator that logs the execution time of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        # print(f"Executed {func.__name__} in {execution_time:.4f} seconds")
        exec_time_logger.info(f"Executed {func.__name__} in {execution_time:.4f} seconds")
        return result
    return wrapper