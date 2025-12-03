# mypy: disable-error-code="import-untyped"
# pylint: disable=E1129, W1203
"""pgvector database utilities for aithena-services."""
import logging
from typing import Optional

import asyncpg
import orjson
from aithena_services.config import (
    IVFFLAT_PROBES,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    AITHENA_LOG_LEVEL,
)

logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)

# Connection pool - will be initialized at startup
_pool: Optional[asyncpg.Pool] = None

# Allowed embedding tables for similarity search
ALLOWED_EMBEDDING_TABLES = {
    "openalex.abstract_embeddings_arctic",
    # Add other allowed embedding tables here as needed
}

# Supported language codes for filtering
SUPPORTED_LANGUAGES = {
    "en",
    "de",
    "es",
    "ja",
    "fr",
    "zh-cn",
    "ko",
    "pt",
    "ru",
    "it",
    "pl",
    "nl",
    "zh-tw",
}

# Language name to code mapping for common variations
LANGUAGE_NAME_TO_CODE = {
    # English variations
    "english": "en",
    "English": "en",
    "ENGLISH": "en",
    # German variations
    "german": "de",
    "German": "de",
    "GERMAN": "de",
    "deutsch": "de",
    "Deutsch": "de",
    # Spanish variations
    "spanish": "es",
    "Spanish": "es",
    "SPANISH": "es",
    "español": "es",
    "Español": "es",
    # French variations
    "french": "fr",
    "French": "fr",
    "FRENCH": "fr",
    "français": "fr",
    "Français": "fr",
    # Japanese variations
    "japanese": "ja",
    "Japanese": "ja",
    "JAPANESE": "ja",
    # Chinese variations
    "chinese": "zh-cn",
    "Chinese": "zh-cn",
    "CHINESE": "zh-cn",
    "chinese-simplified": "zh-cn",
    "chinese_simplified": "zh-cn",
    "chinese-traditional": "zh-tw",
    "chinese_traditional": "zh-tw",
    # Korean variations
    "korean": "ko",
    "Korean": "ko",
    "KOREAN": "ko",
    # Portuguese variations
    "portuguese": "pt",
    "Portuguese": "pt",
    "PORTUGUESE": "pt",
    "português": "pt",
    "Português": "pt",
    # Russian variations
    "russian": "ru",
    "Russian": "ru",
    "RUSSIAN": "ru",
    # Italian variations
    "italian": "it",
    "Italian": "it",
    "ITALIAN": "it",
    "italiano": "it",
    "Italiano": "it",
    # Polish variations
    "polish": "pl",
    "Polish": "pl",
    "POLISH": "pl",
    # Dutch variations
    "dutch": "nl",
    "Dutch": "nl",
    "DUTCH": "nl",
    "nederlands": "nl",
    "Nederlands": "nl",
}


async def init_pool(
    min_size: int = 10,
    max_size: int = 20,
    max_queries: int = 50000,
    max_inactive_connection_lifetime: float = 300.0,
) -> asyncpg.Pool:
    """Initialize the connection pool."""
    global _pool

    if _pool is not None:
        logger.warning("Pool already initialized, closing existing pool")
        await close_pool()

    # Define connection setup function
    async def setup_connection(conn):
        # Set ivfflat probes if configured
        if IVFFLAT_PROBES:
            await conn.execute(f"SET ivfflat.probes = {IVFFLAT_PROBES}")
            logger.debug(f"Set ivfflat.probes = {IVFFLAT_PROBES}")

    logger.info(
        f"Initializing asyncpg connection pool to {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    _pool = await asyncpg.create_pool(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
        min_size=min_size,
        max_size=max_size,
        max_queries=max_queries,
        max_inactive_connection_lifetime=max_inactive_connection_lifetime,
        command_timeout=60,
        statement_cache_size=100,  # Cache prepared statements
        setup=setup_connection,  # Set up each connection with ivfflat.probes
        server_settings={
            "jit": "off",  # Disable JIT for short queries
            "random_page_cost": "1.1",  # Optimized for SSD
        },
    )

    # Test the connection and log database info
    async with _pool.acquire() as conn:
        current_db = await conn.fetchval("SELECT current_database()")
        schemas = await conn.fetch(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema') ORDER BY schema_name"
        )
        schema_list = [r["schema_name"] for r in schemas]

        logger.info(f"Connection pool initialized successfully")
        logger.info(f"Connected to database: {current_db}")
        logger.info(f"Available schemas: {schema_list}")
        if IVFFLAT_PROBES:
            logger.info(f"IVFFlat probes set to: {IVFFLAT_PROBES}")

        # Check if openalex schema exists and has the expected table
        if "openalex" in schema_list:
            tables = await conn.fetch(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'openalex' 
                AND table_name LIKE '%embedding%'
                ORDER BY table_name
            """
            )
            table_list = [r["table_name"] for r in tables]
            logger.info(f"Embedding tables in openalex schema: {table_list}")

    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Connection pool closed")


def get_pool() -> asyncpg.Pool:
    """Get the connection pool. Raises RuntimeError if pool not initialized."""
    if _pool is None:
        raise RuntimeError("Connection pool not initialized. Call init_pool() first.")
    return _pool


def normalize_language_codes(languages: list[str]) -> list[str]:
    """
    Normalize language inputs to supported ISO language codes.

    Args:
        languages: List of language codes or names to normalize

    Returns:
        List of normalized ISO language codes

    Raises:
        ValueError: If any language is not supported
    """
    normalized = []

    for lang in languages:
        # First check if it's already a supported code
        if lang in SUPPORTED_LANGUAGES:
            normalized.append(lang)
        # Then check if it's a known language name variation
        elif lang in LANGUAGE_NAME_TO_CODE:
            normalized.append(LANGUAGE_NAME_TO_CODE[lang])
        # Try lowercase version
        elif lang.lower() in SUPPORTED_LANGUAGES:
            normalized.append(lang.lower())
        else:
            # Last attempt: check if lowercase is in name mapping
            lang_lower = lang.lower()
            if lang_lower in LANGUAGE_NAME_TO_CODE:
                normalized.append(LANGUAGE_NAME_TO_CODE[lang_lower])
            else:
                raise ValueError(
                    f"Unsupported language: '{lang}'. "
                    f"Supported codes: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
                )

    return normalized


async def works_by_similarity_search(
    table_name: str,
    vector: list[float],
    limit: int,
    languages: Optional[list[str]] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> list[dict]:
    """
    Search for similar works with optional filtering by language and publication year.
    Uses prepared statements and optimized query structure for better performance.

    Args:
        table_name (str): The name of the table to search in. Must be in ALLOWED_EMBEDDING_TABLES.
        vector (list[float]): The vector to search for similarities.
        limit (int): The maximum number of similar vectors to return.
        languages (list[str], optional): List of language codes to filter by.
        start_year (int, optional): The minimum publication year (inclusive).
        end_year (int, optional): The maximum publication year (inclusive).

    Returns:
        list[dict]: A list of dicts containing the works data with authorships.

    Raises:
        ValueError: If table_name is not allowed, a language is not supported, or year filters are invalid.
    """
    # Validate table name to prevent SQL injection
    if table_name not in ALLOWED_EMBEDDING_TABLES:
        logger.error(
            f"Invalid table name: {table_name}. Allowed tables: {ALLOWED_EMBEDDING_TABLES}"
        )
        raise ValueError(
            f"Invalid table name: {table_name}. Must be one of: {', '.join(ALLOWED_EMBEDDING_TABLES)}"
        )

    # Validate year filters
    if start_year and end_year and start_year > end_year:
        raise ValueError("start_year cannot be greater than end_year.")

    # Normalize language codes if provided
    normalized_languages = None
    if languages:
        try:
            normalized_languages = normalize_language_codes(languages)
            logger.debug(f"Normalized languages: {languages} -> {normalized_languages}")
        except ValueError as e:
            logger.error(f"Language normalization failed: {e}")
            raise

    # Dynamically build the WHERE clause and parameters
    params = [f"[{','.join(map(str, vector))}]", limit]
    where_clauses = []

    param_idx = 3  # Start parameter index after vector and limit

    if normalized_languages:
        where_clauses.append(f"w.language = ANY(${param_idx}::text[])")
        params.append(normalized_languages)
        param_idx += 1

    if start_year is not None:
        where_clauses.append(f"w.publication_year >= ${param_idx}")
        params.append(start_year)
        param_idx += 1

    if end_year is not None:
        where_clauses.append(f"w.publication_year <= ${param_idx}")
        params.append(end_year)
        param_idx += 1

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    logger.info(f"Where SQL: {where_sql}")

    # Construct the final query
    query_template = f"""
    WITH selected_work_ids AS (
        SELECT 
            emb.work_id,
            emb.embedding <=> $1::vector AS distance
        FROM {table_name} emb
        JOIN openalex.works w ON w.id = emb.work_id
        {where_sql}
        ORDER BY distance
        LIMIT $2
    )
    SELECT 
        w.id,
        w.title,
        w.abstract,
        w.publication_year,
        w.doi,
        w.language,
        1 - s.distance AS similarity_score,
        COALESCE(auth.authorships, '[]'::json) as authorships
    FROM selected_work_ids s
    JOIN openalex.works w ON w.id = s.work_id
    LEFT JOIN LATERAL (
        SELECT json_agg(
            json_build_object(
                'author_position', wa.author_position,
                'author_id', wa.author_id,
                'display_name', a.display_name
            ) ORDER BY wa.author_position
        ) as authorships
        FROM openalex.works_authorships wa
        JOIN openalex.authors a ON wa.author_id = a.id
        WHERE wa.work_id = w.id
    ) auth ON true
    ORDER BY s.distance;
    """

    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            logger.debug(f"Executing query with params: {params[1:]}")
            prepared_stmt = await conn.prepare(query_template)
            rows = await prepared_stmt.fetch(*params)

            results = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "abstract": row["abstract"],
                    "publication_year": row["publication_year"],
                    "doi": row["doi"],
                    "language": row["language"],
                    "similarity_score": row["similarity_score"],
                    "authorships": (
                        orjson.loads(row["authorships"]) if row["authorships"] else []
                    ),
                }
                for row in rows
            ]

            logger.info(f"Found {len(results)} similar works with current filters.")
            return results

        except Exception as e:
            logger.error(f"Error during similarity search: {e}", exc_info=True)
            raise


async def get_article_by_doi(
    doi: str,
) -> list[dict]:
    """Get an article by its DOI.

    Args:
        doi: DOI identifier. Must start with "https://doi.org/10." or "10."

    Returns:
        List of article records with authorships

    Raises:
        ValueError: If DOI format is invalid
    """
    # Validate and normalize DOI
    doi_lower = doi.lower()

    if doi_lower.startswith("10."):
        # Prepend https://doi.org/ to bare DOI
        normalized_doi = f"https://doi.org/{doi}"
    elif doi_lower.startswith("https://doi.org/10."):
        # Already in full format
        normalized_doi = doi
    else:
        raise ValueError(
            f"Invalid DOI format: '{doi}'. "
            "DOI must start with 'https://doi.org/10.' or '10.'"
        )

    # Normalize to lowercase for case-insensitive search
    normalized_doi_lower = normalized_doi.lower()

    pool = get_pool()
    async with pool.acquire() as conn:
        query = f"""
        SELECT
            works.id,
            works.title,
            works.abstract,
            works.publication_year,
            works.doi,
            works.language,
            COALESCE(auth.authorships, '[]'::json) as authorships
        FROM openalex.works works
        LEFT JOIN LATERAL (
            SELECT json_agg(
                json_build_object(
                    'author_position', wa.author_position,
                    'author_id', wa.author_id,
                    'display_name', a.display_name
                ) ORDER BY wa.author_position
            ) as authorships
            FROM openalex.works_authorships wa
            JOIN openalex.authors a ON wa.author_id = a.id
            WHERE wa.work_id = works.id
        ) auth ON true
        WHERE works.doi = $1
        ORDER BY works.publication_year DESC;
        """
        prepared_stmt = await conn.prepare(query)

        # Try lowercase version first
        rows = await prepared_stmt.fetch(normalized_doi_lower)

        # If no results with lowercase, try original case
        if not rows:
            rows = await prepared_stmt.fetch(normalized_doi)

        return [row for row in rows]
