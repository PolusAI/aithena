# mypy: disable-error-code="import-untyped"
# pylint: disable=E1129, W1203
"""pgvector database utilities for aithena-services."""
import re

import psycopg
from aithena_services.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)
from openalex_types import Work
from polus.aithena.common.logger import get_logger

logger = get_logger("aithena_services.memory.pgvector")

DB_CONFIG_STRING = f"dbname={POSTGRES_DB} user={POSTGRES_USER} "
DB_CONFIG_STRING += (
    f"port={POSTGRES_PORT} host={POSTGRES_HOST} password={POSTGRES_PASSWORD}"
)


def return_query_full_work(table_name: str, vector: list[float], limit: int) -> str:
    """Return query for full work."""
    query = f"""
    WITH limited_works AS (
    SELECT works.id
    FROM {table_name} AS emb
    JOIN openalex.works AS works
        ON emb.work_id = works.id
    ORDER BY emb.embedding <=> '{vector}'
    LIMIT {limit}
    ) --- CTE: do this first to limit the number of works
    SELECT
        jsonb_agg(
            jsonb_strip_nulls(
                row_to_json(works)::jsonb || jsonb_build_object(
                    'primary_location', (
                        SELECT row_to_json(works_primary_locations)::jsonb
                        FROM openalex.works_primary_locations AS works_primary_locations
                        WHERE works_primary_locations.work_id = works.id
                    ),
                    'locations', (
                        SELECT jsonb_agg(row_to_json(works_locations)::jsonb)
                        FROM openalex.works_locations AS works_locations
                        WHERE works_locations.work_id = works.id
                    ),
                    'best_oa_location', (
                        SELECT row_to_json(works_best_oa_location)::jsonb
                        FROM openalex.works_best_oa_locations AS works_best_oa_location
                        WHERE works_best_oa_location.work_id = works.id
                    ),
                    'authorships', (
                        SELECT jsonb_agg(row_to_json(works_authorships)::jsonb)
                        FROM openalex.works_authorships AS works_authorships
                        WHERE works_authorships.work_id = works.id
                    ),
                    'biblio', (
                        SELECT row_to_json(works_biblio)::jsonb
                        FROM openalex.works_biblio AS works_biblio
                        WHERE works_biblio.work_id = works.id
                    ),
                    'topics', (
                        SELECT jsonb_agg(row_to_json(works_topics)::jsonb)
                        FROM openalex.works_topics AS works_topics
                        WHERE works_topics.work_id = works.id
                    ),
                    'concepts', (
                        SELECT jsonb_agg(row_to_json(works_concepts)::jsonb)
                        FROM openalex.works_concepts AS works_concepts
                        WHERE works_concepts.work_id = works.id
                    ),
                    'ids', (
                        SELECT row_to_json(works_ids)::jsonb
                        FROM openalex.works_ids AS works_ids
                        WHERE works_ids.work_id = works.id
                    ),
                    'mesh', (
                        SELECT jsonb_agg(row_to_json(works_mesh)::jsonb)
                        FROM openalex.works_mesh AS works_mesh
                        WHERE works_mesh.work_id = works.id
                    ),
                    'open_access', (
                        SELECT row_to_json(works_open_access)::jsonb
                        FROM openalex.works_open_access AS works_open_access
                        WHERE works_open_access.work_id = works.id
                    ),
                    'referenced_works', (
                        SELECT jsonb_agg(row_to_json(works_referenced_works)::jsonb)
                        FROM openalex.works_referenced_works AS works_referenced_works
                        WHERE works_referenced_works.work_id = works.id
                    ),
                    'related_works', (
                        SELECT jsonb_agg(row_to_json(works_related_works)::jsonb)
                        FROM openalex.works_related_works AS works_related_works
                        WHERE works_related_works.work_id = works.id
                    )
                )
            )
        ) AS full_work
    FROM limited_works
    JOIN openalex.works AS works
        ON limited_works.id = works.id
    """
    return query


def similarity_search(
    table_name: str,
    vector: list[float],
    limit: int,
    full: bool = False,
) -> list[Work]:
    """
    Search for similar works.

    If full is set to True, the full Work object is returned.
    If full is set to False, only the basic work metadata with
    authorships is returned.

    Args:
        table_name (str): The name of the table to search in.
        vector (list[float]): The vector to search for similarities.
        limit (int, optional): The maximum number of similar vectors to return.
        full (bool, optional): Whether to query and return the full Work object.

    Returns:
        list[Work]: A list of Work objects as dict.
    """
    if not full:
        query = f"""
        WITH limited_works AS (
        SELECT works.id
        FROM {table_name} AS emb
        JOIN openalex.works AS works
            ON emb.work_id = works.id
        ORDER BY emb.embedding <=> '{vector}'
        LIMIT {limit}
        )
        SELECT
            row_to_json(works)::jsonb || jsonb_build_object(
                'authorships',
                CASE
                    WHEN COUNT(works_authorships.work_id) = 0 THEN NULL
                    ELSE json_agg(
                        DISTINCT json_build_object(
                            'author', json_build_object(
                                'display_name', authors.display_name,
                                'id', works_authorships.author_id
                            )::jsonb
                        )::jsonb
                    )
                END
            ) AS work_with_authorships
        FROM limited_works
        JOIN openalex.works AS works
            ON limited_works.id = works.id
        LEFT JOIN openalex.works_authorships AS works_authorships
            ON works.id = works_authorships.work_id
        LEFT JOIN openalex.authors AS authors
            ON works_authorships.author_id = authors.id
        GROUP BY works.id;  
        """
    else:
        query = return_query_full_work(table_name, vector, limit)

    with psycopg.connect(DB_CONFIG_STRING) as conn:
        with conn.cursor() as cur:
            try:
                query_to_log = re.sub(r"\[.*?\]", "[...]", query)
                logger.debug(
                    f"Performing similarity search with query: {query_to_log}")
                cur.execute(query)
                res = cur.fetchall()

                if full:
                    works = [Work(**w) for w in res[0][0]]
                else:
                    works = [Work(**w[0]) for w in res]
            except Exception as e:
                logger.error(f"Error when performing similarity search: {e}")
                raise e

    return works


def work_ids_by_similarity_search(
    table_name: str,
    vector: list[float],
    limit: int,
) -> list[str]:
    """
    Search for similar works and return only id.

    Args:
        table_name (str): The name of the table to search in.
        vector (list[float]): The vector to search for similarities.
        limit (int, optional): The maximum number of similar vectors to return.

    Returns:
        list[str]: A list of IDs of the similar vectors found.
    """
    query = f"""
    SELECT work_id
    FROM {table_name}
    ORDER BY embedding <=> '{vector}' LIMIT {limit};
    """

    with psycopg.connect(DB_CONFIG_STRING) as conn:
        with conn.cursor() as cur:
            try:
                query_to_log = re.sub(r"\[.*?\]", "[...]", query)
                logger.debug(
                    f"Performing similarity search with query: {query_to_log}")
                cur.execute(query)
                res = cur.fetchall()
                res_to_return = [r[0] for r in res]
            except Exception as e:
                logger.error(f"Error when performing similarity search: {e}")
                raise e

    return res_to_return


def works_by_similarity_search(
    table_name: str,
    vector: list[float],
    limit: int,
) -> list[Work]:
    """
    Search for similar works and return just basic work metadata.

    Args:
        table_name (str): The name of the table to search in.
        vector (list[float]): The vector to search for similarities.
        limit (int, optional): The maximum number of similar vectors to return.

    Returns:
        list[str]: A list of IDs of the similar vectors found.
    """
    query = f"""
    WITH selected_work_ids AS (
    SELECT work_id
    FROM {table_name}
    ORDER BY embedding <=> '{vector}' LIMIT {limit}
    )
    SELECT w.*
    FROM openalex.works w
    JOIN selected_work_ids s ON w.id = s.work_id;
    ;
    """

    with psycopg.connect(DB_CONFIG_STRING) as conn:
        with conn.cursor() as cur:
            try:
                query_to_log = re.sub(r"\[.*?\]", "[...]", query)
                logger.debug(
                    f"Performing similarity search with query: {query_to_log}")
                cur.execute(query)
                res = cur.fetchall()
                works = [Work.from_sql(work) for work in res]
            except Exception as e:
                logger.error(f"Error when performing similarity search: {e}")
                raise e

    return works
