"""Ask Aithena agent module."""
# pylint: disable=W1203
from typing import Optional

import httpx
import requests
from polus.aithena.ask_aithena import config
from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import time_logger
from pydantic import BaseModel

logger = get_logger(__name__)


class AskAithenaQuery(BaseModel):
    """Aithena query."""

    query: str


class AskAithenaResponse(BaseModel):
    """Aithena response."""

    response: str


def work_to_context(work: dict) -> str:
    """Convert work dict to context."""
    context_string = "<doc>\n"
    context_string += f"<id>{work['id']}</id>\n"
    context_string += f"<text>{work['abstract']}</text>\n"
    return context_string


def work_to_reference(work: dict) -> str:
    """Convert work dict to reference."""
    if work.get("authorships") is None:
        authors_ = ""
    else:
        authors = [author["author"]["display_name"]
                for author in work["authorships"]]
        authors = [author for author in authors if author is not None]
        authors_ = ", ".join(authors)
    year_ = work["publication_year"] or ""
    doi_ = work["doi"] or ""
    ref = f"{authors_}, {work['title']} <br/> Year: {year_} <br/>"
    ref += f"DOI: {doi_} <br/>\n\n"
    return ref


class Context(BaseModel):
    """Context for a llm conversation."""

    docs: list[dict] = []

    def to_llm(self) -> str:
        """Convert context before sending to llm."""
        works = "<br>".join([work_to_context(doc) for doc in self.docs])
        return f"""<{config.CONTEXT_TAG}>{works}</{config.CONTEXT_TAG}>"""

    def to_reference(self):
        """Convert context to reference format."""
        ref = "\n".join(
            [f"({i+1}) {work_to_reference(doc)}" for i,
                doc in enumerate(self.docs)]
        )
        return ref


@ time_logger
def embed_request(text):
    """Embed text using the embedding model."""
    url = config.AITHENA_SERVICE_URL + f"/embed/{config.EMBED_MODEL}/generate"
    logger.debug(f"embedding query at {url}")

    try:
        response = requests.post(url, json=text)
        response.raise_for_status()  # Raise an error for bad status codes
        result = response.json()
        return result
    except requests.RequestException as e:
        msg = (f"Embedding Error: {url}.", f"Got response: {e}")
        raise requests.RequestException(msg)


@ time_logger
def vector_search_request(
    vector: list[float],
    table: Optional[str] = config.EMBEDDING_TABLE,
    n: Optional[int] = config.SIMILARITY_N,
    ) -> list[dict]:
    """Search for similar vectors in the database."""
    logger.debug("searching for similar vectors in the database.")
    url = config.AITHENA_SERVICE_URL + "/memory/pgvector/search"
    try:
        res = requests.post(url, json=vector,
                            params={
                                "table_name": table,
                                "n": n},
                            timeout=config.TIMEOUT
                            ).json()
    except Exception as e:
        msg = f"Got response: {e}"
        logger.error(f"{msg}")
        raise requests.RequestException(msg)
    logger.debug("successfully got similar works from db.")

    return res


@ time_logger
def chat_request(messages: list[dict]):
    """Chat with the model."""
    url = config.AITHENA_SERVICE_URL + f"/chat/{config.CHAT_MODEL}/generate"
    logger.debug(f"request answer from {url}")
    try:
        response = requests.post(
            url, json=messages, params={"stream": False}, stream=False,
            timeout=config.TIMEOUT
        )
    except requests.RequestException as e:
        msg = (f"Chat Error: {url}.", f"Got response: {e}")
        raise requests.RequestException(msg)
    response.raise_for_status()  # Raise an error for bad status codes
    result = response.json()
    return result


# TODO why not use that in fastapi?
async def chat_request_stream(messages: list[dict]):
    """Chat with model and stream response."""
    url = config.AITHENA_SERVICE_URL + f"/chat/{config.CHAT_MODEL}/generate"
    logger.debug(f"request streaming answer from {url}")

    async def stream_generator():
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0)) as client:
            async with client.stream(
                "POST", url, json=messages, params={"stream": True}
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        print(line)
                        yield line + "\n"

    return stream_generator()


@ time_logger
def ask(query: AskAithenaQuery) -> AskAithenaResponse:
    """Ask Aithena and return full response."""
    logger.debug(f"ask aithena stream=False: {query}")
    embedding = embed_request(query.query)
    works = vector_search_request(embedding)
    context = Context(docs=works)
    context_string = context.to_llm()
    system_message = config.SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system_message + context_string},
        {"role": "user", "content": query.query},
    ]
    resp = chat_request(messages)
    # python word count
    word_count = len(resp["message"]["content"].split())
    response_to_return = f"{resp['message']['content']} [Word Count:{word_count}]"
    response_to_return += f" \n\n **References:**<br/> {context.to_reference()}"
    return AskAithenaResponse(response=response_to_return)


def ask_stream(query: AskAithenaQuery) -> tuple[list[dict], str]:
    """Ask Aithena and stream back response chunks."""
    logger.debug(f"ask aithena stream=True: {query}")
    embedding = embed_request(query.query)
    works = vector_search_request(embedding)
    context = Context(docs=works)
    context_string = context.to_llm()
    system_message = config.SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system_message + context_string},
        {"role": "user", "content": query.query},
    ]
    references = f"\n\n **References:**<br/> {context.to_reference()}"

    # TODO move http async here?
    return messages, references
