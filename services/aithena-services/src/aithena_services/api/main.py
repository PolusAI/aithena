# mypy: disable-error-code="import-untyped"
"""Aithena-Services FastAPI REST Endpoints. """

# pylint: disable=W1203, C0412, C0103, W0212, W0707, W0718

from aithena_services.memory.pgvector import (
    similarity_search,
    work_ids_by_similarity_search,
    works_by_similarity_search,
)
from fastapi import FastAPI, HTTPException
from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import time_logger

logger = get_logger("aithena_services.api")


app = FastAPI()


@time_logger
@app.post("/memory/pgvector/search")
def search_pgvector(
    table_name: str,
    vector: list[float],
    n: int = 10,
    full: bool = False,
):
    """
    Search for similar vectors in a specified table using pgvector with cosine distance.

    Args:
        table_name (str): The name of the table to search in.
        vector (list[float]): The vector to search for similar vectors.
        n (int, optional): The number of similar vectors to return. Defaults to 10.
        full (bool, optional): Whether to return the full Work object. Defaults to False.

    Returns:
        The result of the similarity search as a list of Work objects.

    Raises:
        HTTPException: If there is an error during the similarity search.
    """
    try:
        res = similarity_search(table_name, vector, n, full)
    except Exception as exc:
        logger.error(f"Error in similarity search: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    return res


@time_logger
@app.post("/memory/pgvector/search_work_ids")
def search_work_ids_pgvector(
    table_name: str,
    vector: list[float],
    n: int = 10,
):
    """
    Search for work IDs using pgvector similarity search.

    This function performs a similarity search on
    the specified table using the provided vector and returns the top `n` work IDs.

    Args:
        table_name (str): The name of the table to search in.
        vector (list[float]): The vector to use for the similarity search.
        n (int, optional): The number of top results to return. Defaults to 10.

    Returns:
        list: A list of work IDs that are most similar to the provided vector.

    Raises:
        HTTPException: If an error occurs during the similarity search.
    """
    try:
        res = work_ids_by_similarity_search(table_name, vector, n)
    except Exception as exc:
        logger.error(f"Error in similarity search: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    return res


@time_logger
@app.post("/memory/pgvector/search_works")
def search_works_pgvector(
    table_name: str,
    vector: list[float],
    n: int = 10,
):
    """
    Perform a similarity search on the specified table using a vector.

    Args:
        table_name (str): The name of the table to search.
        vector (list[float]): The vector to use for the similarity search.
        n (int, optional): The number of results to return. Defaults to 10.

    Returns:
        list: The search results.

    Raises:
        HTTPException: If an error occurs during the similarity search.
    """
    try:
        res = works_by_similarity_search(table_name, vector, n)
    except Exception as exc:
        logger.error(f"Error in similarity search: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    return res
