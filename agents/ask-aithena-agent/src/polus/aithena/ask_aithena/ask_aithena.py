"""Ask Aithena agent module."""

from typing import Optional
import httpx
import qdrant_client
import qdrant_client.http
import qdrant_client.http.exceptions
import requests
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint
from polus.aithena.ask_aithena import config
from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import time_logger

logger = get_logger(__file__)

client = QdrantClient(host=config.DB_HOST, port=config.DB_PORT)


class AskAithenaQuery(BaseModel):
    """Aithena query."""

    query: str


class AskAithenaResponse(BaseModel):
    """Aithena response."""

    response: str


class Author(BaseModel):
    """Base Model for Author."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None
    affiliation: Optional[str] = None

    @classmethod
    def from_record(cls, doc: dict) -> "Author":
        """Create an `Author` from a dictionary coming from a `Record`."""
        affiliation_ = doc.get("affiliation", None)
        if isinstance(affiliation_, list):
            if len(affiliation_) == 0:
                affiliation_ = None
            else:
                affiliation_ = " ".join(affiliation_)

        return cls(
            first_name=doc.get("forenames", None),
            last_name=doc.get("keyname", None),
            suffix=doc.get("suffix", None),
            affiliation=affiliation_,
        )

    def to_reference(self):
        """Convert author to reference format."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name
        return "Unknown Author"


class Document(BaseModel):
    """Document."""

    text: str
    id: str  # UUID Qdrant
    score: float
    title: str
    authors: list[Author]
    date: str
    doi: Optional[str]
    arxiv_id: Optional[str] = None

    # NOTE: this is for arxiv only
    @classmethod
    def from_point(cls, point: ScoredPoint) -> "Document":
        """Create a `Document` from a `ScoredPoint`."""
        doi_ = point.payload.get("doi", None)
        if doi_ and isinstance(doi_, list) and len(doi_) > 0:
            doi_ = doi_[0] if doi_[0] != "" else None
        else:
            doi_ = None
        return cls(
            text=point.payload["abstract"][0],
            id=point.id,
            arxiv_id=point.payload["id"][0],
            score=point.score,
            title=point.payload["title"][0],
            authors=[
                Author.from_record(x) for x in point.payload["authors"][0]["author"]
            ],
            date=point.payload["created"][0],
            doi=doi_,
        )

    def to_llm(self):
        """Convert document before sending to llm."""
        return f"""
                <{config.DOCUMENT_TAG}>
                    <{config.ID_TAG}>{self.id}</{config.ID_TAG}>
                    <{config.TEXT_TAG}>{self.text}</{config.TEXT_TAG}>
                </{config.DOCUMENT_TAG}>
                """

    def to_reference(self):
        """Convert document to reference format."""
        authors_ = "; ".join([author.to_reference() for author in self.authors])
        year_ = self.date.split("-")[0]

        # generate doi from arxiv id if not present
        doi_ = (
            (f"https://doi.org/10.48550/arXiv.{self.arxiv_id}" if self.arxiv_id else "")
            if not self.doi
            else f"https://doi.org/{self.doi}"
        )

        ref = f"{authors_}, {self.title} <br/> Year: {year_} <br/>"
        ref += f"DOI: {doi_} <br/> Relevance: {self.score:.3f}\n\n"
        return ref


class Context(BaseModel):
    """Context for a llm conversation."""

    docs: list[Document] = []

    def to_llm(self) -> str:
        """Convert context before sending to llm."""
        records = "<br>".join([doc.to_llm() for doc in self.docs])
        return f"""<{config.CONTEXT_TAG}>{records}</{config.CONTEXT_TAG}>"""

    def to_reference(self):
        """Convert context to reference format."""
        ref = "\n".join(
            [f"({i+1}) {doc.to_reference()}" for i, doc in enumerate(self.docs)]
        )
        return ref


@time_logger
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


@time_logger
def vector_search_request(vector: list[float]) -> list[ScoredPoint]:
    """Search for similar vectors in the database."""
    # TODO change to URL
    logger.debug(
        (
            f"retrieve relevant documents from {config.DOC_COLLECTION}",
            f"at: {config.DB_HOST}:{config.DB_PORT}",
        )
    )
    try:
        res = client.query_points(collection_name=config.DOC_COLLECTION, query=vector)
    except qdrant_client.http.exceptions.ResponseHandlingException as e:
        msg = (f"DB Error: {config.DB_HOST}:{config.DB_PORT}.", f"Got response: {e}")
        logger.error(f"{msg}")
        raise requests.RequestException(msg)

    logger.debug(f"{len(res.points)} docs retrieved.")
    return res.points


@time_logger
def chat_request(messages: list[dict]):
    """Chat with the model."""
    url = config.AITHENA_SERVICE_URL + f"/chat/{config.CHAT_MODEL}/generate"
    logger.debug(f"request answer from {url}")
    try:
        response = requests.post(
            url, json=messages, params={"stream": False}, stream=False
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


@time_logger
def ask(query: AskAithenaQuery) -> AskAithenaResponse:
    """Ask Aithena and return full response."""
    logger.debug(f"ask aithena stream=False: {query}")
    embedding = embed_request(query.query)
    points = vector_search_request(embedding)
    texts = [Document.from_point(point) for point in points]
    context = Context(docs=texts)
    context_string = context.to_llm()
    context_string = "context string is a lot of blabla"
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
    points = vector_search_request(embedding)
    texts = [Document.from_point(point) for point in points]
    context = Context(docs=texts)
    context_string = context.to_llm()
    system_message = config.SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system_message + context_string},
        {"role": "user", "content": query.query},
    ]
    references = f"\n\n **References:**<br/> {context.to_reference()}"

    # TODO move http async here?
    return messages, references
