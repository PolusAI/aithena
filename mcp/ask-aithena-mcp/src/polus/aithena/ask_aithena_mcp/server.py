import os
from typing import Annotated, Optional
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import Field
import httpx
import logging

logger = logging.getLogger(__name__)


load_dotenv(override=True)
ASKAITHENA_API_URL = os.getenv("ASKAITHENA_API_URL")

mcp = FastMCP(name="AskAithena", instructions="Ask Aithena is a tool that allows you to search for scientific articles based on a query.", debug=True)

@mcp.tool("get_articles")
async def get_articles(
    query: Annotated[str, Field(description="The query to search for: usually a question.")],
    langs: Annotated[list[str], Field(description="The languages of the articles to retrieve")] = ['en'],
    start_year: Annotated[int, Field(description="The start year of the articles to retrieve.")] = -1,
    end_year: Annotated[int, Field(description="The end year of the articles to retrieve.")] = -1,
    n: Annotated[int, Field(description="The number of articles to retrieve.")] = 10,
    # query: str,
    # langs: list[str] = ['en'],
    # start_year: int = None,
    # end_year: int = None,
    # n: int = 10,
):
    """Retrieve articles based on similarity search with `query`.

    Example use cases:
    - User asks for articles based on a specific query.
    - User asks for help finding articles related to a specific topic.
    - User wants to retrieve articles related to a question and user wants to filter by language and/or year.

    For example, user says: "What are the best way to calculate the area of a circle?", then that question is the `query`.
    
    You can filter the results by language, using the ISO 639-1 format or the language name in English.
    For example: ['en', 'spanish'] or ['English', 'Spanish'] or ['en', 'es'].
    If you want to retrieve all languages, you must use `['all']`.

    You can filter the results by year of publication.
    There is `start_year` and `end_year`: they are both integers and they are inclusive.
    For example, to retrieve articles published between 2020 and 2023, you can use:
    `start_year=2020` and `end_year=2023`.
    -1 is equivalent to `null` for `start_year` and `end_year`.

    You can also specify the number of articles to retrieve (`n`) and this will be the top `n` articles that are most similar to the query.

    **Default values:** by default, we are retrieving 10 articles, ONLY in English, without filtering by year.

    Args:
        query: The query to search for: usually a question.
        langs: The languages of the articles to retrieve, can be ['es'] or ['English', 'Spanish'] or ['en', 'es']. Default is ['en'].
        start_year: The start year of the articles to retrieve. Default is -1. It must be an integer. If you want to set it to `null`, you must use `-1`.
        end_year: The end year of the articles to retrieve. Default is -1. It must be an integer. If you want to set it to `null`, you must use `-1`.
        n: The number of articles to retrieve. Default is 10.

    Returns:
        A list of articles with title, OpenAlex ID, year, similarity score, and abstract in JSON format.
    """
    logger.info(f"Received get_articles request with query: {query}, langs: {langs}, start_year: {start_year}, end_year: {end_year}, n: {n}")
    if start_year == -1:
        start_year = None
    if end_year == -1:
        end_year = None
    if langs == ['all'] or langs == ['All'] or langs == ['ALL']:
        langs = None
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{ASKAITHENA_API_URL}/get-articles",
            json={
                "query": query,
                "similarity_n": n,
                "languages": langs,
                "start_year": start_year,
                "end_year": end_year,
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool("get_article_by_doi")
async def get_article_by_doi(
    doi: Annotated[str, "DOI identifier. Must start with 'https://doi.org/10.' or '10.'"],
):
    """Retrieve an article by its DOI.

    Example use cases:
    - User asks for an article by its DOI.
    - User wants to retrieve an article by its DOI and get the authorships.
    - User wants information about an article and user gives you the DOI.

    For example: 'Who wrote the article with the DOI 10.1038/s41598-021-91234-y?'
    Or 'What is the abstract of the article with the DOI 10.1038/s41598-021-91234-y?'
    Or 'What is the title of the article with the DOI 10.1038/s41598-021-91234-y?'...

    Returns:
        A list of articles with title, OpenAlex ID, year, similarity score, and abstract in JSON format.
        Most of the time, the list will contain only one article, but OpenAlex could return multiple articles with the same DOI
        in some edge cases. The list will be ordered by the year of publication, descending.
    """
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{ASKAITHENA_API_URL}/get-article-by-doi",
            json={"doi": doi},
        )
        response.raise_for_status()
        return response.json()



@mcp.tool("get_semantic_query")
async def get_semantic_query(
    text: Annotated[str, Field(description="The text to extract the semantic query from.")],
):
    """
    Transforms a natural language query into a sentence optimized for semantic vector search.

    This tool acts as a sophisticated "translator." It analyzes a user's question,
    extracts the main ideas and keywords, and constructs a neutral, unbiased sentence.
    Its primary function is to improve the quality of search results for tools like `get_articles`
    by providing a query that is dense with semantic meaning. It does NOT answer the user's question.

    Key Features & Considerations:
    - Removes conversational filler and politeness.
    - Expands common acronyms to their full form (e.g., "NLP" to "Natural Language Processing").
    - Cohesively merges multi-part questions into a single sentence.
    - Maintains neutrality and avoids introducing any information not present in the original query.

    Use Cases:
    - Before using the `get_articles` tool to refine a complex user query into a more effective search term.
    - When the user's query is long, conversational, or contains multiple questions.
    - To generate a "search-friendly" version of a user's question.

    Examples:
    - Input: "I'm a doctor and I need to know what is the best treatment for diabetes in patients with hypertension."
    - Output: "Optimal treatment protocols for diabetes in patients with comorbid hypertension."

    - Input: "Is it true that the sky is blue?"
    - Output: "The scientific explanation for the blue color of the sky."

    Args:
        text: The natural language query to be transformed.

    Returns:
        A JSON string containing the processed semantic query.
    """
    logger.info(f"Received get_semantic_query request with text: {text}")
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{ASKAITHENA_API_URL}/get-semantic-query",
            json={"query": text},
        )
        response.raise_for_status()
        return response.json()

@mcp.prompt("prompt_owl")
async def prompt_owl(
    query: Annotated[str, Field(description="What do you want to know?")],
    langs: Annotated[list[str], Field(description="The languages of the articles to retrieve, default is only English.")] = ['en'],
    start_year: Annotated[int, Field(description="The start year of the articles to retrieve.")] = -1,
    end_year: Annotated[int, Field(description="The end year of the articles to retrieve.")] = -1,
    n: Annotated[int, Field(description="The number of articles to retrieve.")] = 10,
):
    """
    Generates a prompt to answer a question based on scientific evidence.

    Owl mode is designed for direct, evidence-based answers. It works in two stages:
    1.  It retrieves a set of scientific articles relevant to the user's query using a similarity search.
    2.  It then uses a large language model to generate a comprehensive answer based *only* on the information contained within the retrieved articles.

    This is the base level of answering. More robust modes, "Shield" and "Aegis," which will include additional layers of analysis and reranking, will be added later.

    Use Cases:
    - When a user asks a question and expects a detailed, evidence-based answer.
    - To generate a summary of research on a specific topic, backed by citations.

    For example: Can you help me find the best way to calculate the area of a circle based on scientific evidence?
    You could use this prompt passing query="Can you help me find the best way to calculate the area of a circle based on scientific evidence?"
    and langs=['en'], start_year=-1, end_year=-1, n=10.

    Args:
        query: The user's question.
        langs: The languages of the articles to retrieve. Default is ['en'].
        start_year: The start year for filtering articles. Default is -1 (no filter).
        end_year: The end year for filtering articles. Default is -1 (no filter).
        n: The number of articles to retrieve as context. Default is 10.

    Returns:
        A prompt with the question and the context to answer the question.
    """
    logger.info(f"Received answer_owl request with query: {query}, langs: {langs}, start_year: {start_year}, end_year: {end_year}, n: {n}")
    if start_year == -1:
        start_year = None
    if end_year == -1:
        end_year = None
    if langs == ['all'] or langs == ['All'] or langs == ['ALL']:
        langs = None
    async with httpx.AsyncClient(timeout=3600) as client:
        response = await client.post(
            f"{ASKAITHENA_API_URL}/prompt-owl",
            json={
                "query": query,
                "similarity_n": n,
                "languages": langs,
                "start_year": start_year,
                "end_year": end_year,
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.prompt("prompt_shield")
async def prompt_shield(
    query: Annotated[str, Field(description="What do you want to know?")],
    langs: Annotated[list[str], Field(description="The languages of the articles to retrieve, default is only English.")] = ['en'],
    start_year: Annotated[int, Field(description="The start year of the articles to retrieve.")] = -1,
    end_year: Annotated[int, Field(description="The end year of the articles to retrieve.")] = -1,
    n: Annotated[int, Field(description="The number of articles to retrieve.")] = 10,
):
    """
    Generates a prompt to answer a question based on scientific evidence using Shield mode.

    Shield mode is an enhanced version of Owl mode that provides more accurate answers through:
    1. It retrieves a set of scientific articles relevant to the user's query using a similarity search.
    2. It adds a reranking step to double-check and ensure the retrieved documents are truly relevant to the question.
    3. It then uses a large language model to generate a comprehensive answer based *only* on the reranked, higher-quality documents.

    The reranking step makes Shield mode more robust than Owl mode by filtering out less relevant documents,
    resulting in more accurate and focused answers.

    Use Cases:
    - When accuracy is more important than speed
    - For complex questions where relevance filtering can improve answer quality
    - When you want higher confidence that the cited documents directly address the question

    Example: Can you help me find the best way to calculate the area of a circle based on scientific evidence?
    You could use this prompt passing query="Can you help me find the best way to calculate the area of a circle based on scientific evidence?"
    and langs=['en'], start_year=-1, end_year=-1, n=10.

    Args:
        query: The user's question.
        langs: The languages of the articles to retrieve. Default is ['en'].
        start_year: The start year for filtering articles. Default is -1 (no filter).
        end_year: The end year for filtering articles. Default is -1 (no filter).
        n: The number of articles to retrieve as context. Default is 10.

    Returns:
        A prompt with the question and the reranked context to answer the question.
    """
    logger.info(f"Received answer_owl request with query: {query}, langs: {langs}, start_year: {start_year}, end_year: {end_year}, n: {n}")
    if start_year == -1:
        start_year = None
    if end_year == -1:
        end_year = None
    if langs == ['all'] or langs == ['All'] or langs == ['ALL']:
        langs = None
    async with httpx.AsyncClient(timeout=3600) as client:
        response = await client.post(
            f"{ASKAITHENA_API_URL}/prompt-shield",
            json={
                "query": query,
                "similarity_n": n,
                "languages": langs,
                "start_year": start_year,
                "end_year": end_year,
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.prompt("prompt_aegis")
async def prompt_aegis(
    query: Annotated[str, Field(description="What do you want to know?")],
    langs: Annotated[list[str], Field(description="The languages of the articles to retrieve, default is only English.")] = ['en'],
    start_year: Annotated[int, Field(description="The start year of the articles to retrieve.")] = -1,
    end_year: Annotated[int, Field(description="The end year of the articles to retrieve.")] = -1,
    n: Annotated[int, Field(description="The number of articles to retrieve.")] = 10,
):
    """
    Generates a prompt to answer a question based on scientific evidence using Aegis mode.

    Aegis mode is the most advanced and robust answering mode, providing the highest accuracy through:
    1. It retrieves a set of scientific articles relevant to the user's query using a similarity search.
    2. It applies a "very careful" reranking process - more rigorous than Shield mode - to ensure maximum relevance.
    3. It then uses a large language model to generate a comprehensive answer based *only* on the most thoroughly vetted documents.

    Aegis mode represents the highest level of quality assurance in document selection, using advanced
    algorithms to meticulously evaluate document relevance before including them in the answer context.

    Use Cases:
    - Critical research questions where accuracy is paramount
    - Medical or scientific inquiries where precision is essential
    - Complex multi-faceted questions requiring the most relevant sources
    - When you need the highest confidence in the accuracy of citations
    - Situations where incorrect information could have serious consequences

    Trade-offs:
    - May be slower than Owl or Shield modes due to more thorough processing
    - Best used when quality matters more than speed

    Example: What are the molecular mechanisms of CRISPR-Cas9 gene editing and its current therapeutic applications?
    You could use this prompt passing query="What are the molecular mechanisms of CRISPR-Cas9 gene editing and its current therapeutic applications?"
    and langs=['en'], start_year=2020, end_year=-1, n=15.

    Args:
        query: The user's question.
        langs: The languages of the articles to retrieve. Default is ['en'].
        start_year: The start year for filtering articles. Default is -1 (no filter).
        end_year: The end year for filtering articles. Default is -1 (no filter).
        n: The number of articles to retrieve as context. Default is 10.

    Returns:
        A prompt with the question and the most carefully vetted context to answer the question.
    """
    logger.info(f"Received answer_aegis request with query: {query}, langs: {langs}, start_year: {start_year}, end_year: {end_year}, n: {n}")
    if start_year == -1:
        start_year = None
    if end_year == -1:
        end_year = None
    if langs == ['all'] or langs == ['All'] or langs == ['ALL']:
        langs = None
    async with httpx.AsyncClient(timeout=3600) as client:
        response = await client.post(
            f"{ASKAITHENA_API_URL}/prompt-aegis",
            json={
                "query": query,
                "similarity_n": n,
                "languages": langs,
                "start_year": start_year,
                "end_year": end_year,
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool("answer_owl")
async def answer_owl(
    query: Annotated[str, Field(description="What do you want to know?")],
    langs: Annotated[list[str], Field(description="The languages of the articles to retrieve, default is only English.")] = ['en'],
    start_year: Annotated[int, Field(description="The start year of the articles to retrieve.")] = -1,
    end_year: Annotated[int, Field(description="The end year of the articles to retrieve.")] = -1,
    n: Annotated[int, Field(description="The number of articles to retrieve.")] = 10,
):
    """
    Generates a prompt to answer a question based on scientific evidence.

    Owl mode is designed for direct, evidence-based answers. It works in two stages:
    1.  It retrieves a set of scientific articles relevant to the user's query using a similarity search.
    2.  It then uses a large language model to generate a comprehensive answer based *only* on the information contained within the retrieved articles.

    This is the base level of answering. More robust modes, "Shield" and "Aegis," which will include additional layers of analysis and reranking, will be added later.

    Use Cases:
    - When a user asks a question and expects a detailed, evidence-based answer.
    - To generate a summary of research on a specific topic, backed by citations.

    For example: Can you help me find the best way to calculate the area of a circle based on scientific evidence?
    You could use this prompt passing query="Can you help me find the best way to calculate the area of a circle based on scientific evidence?"
    and langs=['en'], start_year=-1, end_year=-1, n=10.

    Args:
        query: The user's question.
        langs: The languages of the articles to retrieve. Default is ['en'].
        start_year: The start year for filtering articles. Default is -1 (no filter).
        end_year: The end year for filtering articles. Default is -1 (no filter).
        n: The number of articles to retrieve as context. Default is 10.

    Returns:
        A prompt with the question and the context to answer the question.
    """
    logger.info(f"Received answer_owl request with query: {query}, langs: {langs}, start_year: {start_year}, end_year: {end_year}, n: {n}")
    if start_year == -1:
        start_year = None
    if end_year == -1:
        end_year = None
    if langs == ['all'] or langs == ['All'] or langs == ['ALL']:
        langs = None
    async with httpx.AsyncClient(timeout=3600) as client:
        response = await client.post(
            f"{ASKAITHENA_API_URL}/answer-owl",
            json={
                "query": query,
                "similarity_n": n,
                "languages": langs,
                "start_year": start_year,
                "end_year": end_year,
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool("answer_shield")
async def answer_shield(
    query: Annotated[str, Field(description="What do you want to know?")],
    langs: Annotated[list[str], Field(description="The languages of the articles to retrieve, default is only English.")] = ['en'],
    start_year: Annotated[int, Field(description="The start year of the articles to retrieve.")] = -1,
    end_year: Annotated[int, Field(description="The end year of the articles to retrieve.")] = -1,
    n: Annotated[int, Field(description="The number of articles to retrieve.")] = 10,
):
    """
    Generates a prompt to answer a question based on scientific evidence using Shield mode.

    Shield mode is an enhanced version of Owl mode that provides more accurate answers through:
    1. It retrieves a set of scientific articles relevant to the user's query using a similarity search.
    2. It adds a reranking step to double-check and ensure the retrieved documents are truly relevant to the question.
    3. It then uses a large language model to generate a comprehensive answer based *only* on the reranked, higher-quality documents.

    The reranking step makes Shield mode more robust than Owl mode by filtering out less relevant documents,
    resulting in more accurate and focused answers.

    Use Cases:
    - When accuracy is more important than speed
    - For complex questions where relevance filtering can improve answer quality
    - When you want higher confidence that the cited documents directly address the question

    Example: Can you help me find the best way to calculate the area of a circle based on scientific evidence?
    You could use this prompt passing query="Can you help me find the best way to calculate the area of a circle based on scientific evidence?"
    and langs=['en'], start_year=-1, end_year=-1, n=10.

    Args:
        query: The user's question.
        langs: The languages of the articles to retrieve. Default is ['en'].
        start_year: The start year for filtering articles. Default is -1 (no filter).
        end_year: The end year for filtering articles. Default is -1 (no filter).
        n: The number of articles to retrieve as context. Default is 10.

    Returns:
        A prompt with the question and the reranked context to answer the question.
    """
    logger.info(f"Received answer_owl request with query: {query}, langs: {langs}, start_year: {start_year}, end_year: {end_year}, n: {n}")
    if start_year == -1:
        start_year = None
    if end_year == -1:
        end_year = None
    if langs == ['all'] or langs == ['All'] or langs == ['ALL']:
        langs = None
    async with httpx.AsyncClient(timeout=3600) as client:
        response = await client.post(
            f"{ASKAITHENA_API_URL}/answer-shield",
            json={
                "query": query,
                "similarity_n": n,
                "languages": langs,
                "start_year": start_year,
                "end_year": end_year,
            },
        )
        response.raise_for_status()
        return response.json()

@mcp.tool("answer_aegis")
async def answer_aegis(
    query: Annotated[str, Field(description="What do you want to know?")],
    langs: Annotated[list[str], Field(description="The languages of the articles to retrieve, default is only English.")] = ['en'],
    start_year: Annotated[int, Field(description="The start year of the articles to retrieve.")] = -1,
    end_year: Annotated[int, Field(description="The end year of the articles to retrieve.")] = -1,
    n: Annotated[int, Field(description="The number of articles to retrieve.")] = 10,
):
    """
    Generates a prompt to answer a question based on scientific evidence using Aegis mode.

    Aegis mode is the most advanced and robust answering mode, providing the highest accuracy through:
    1. It retrieves a set of scientific articles relevant to the user's query using a similarity search.
    2. It applies a "very careful" reranking process - more rigorous than Shield mode - to ensure maximum relevance.
    3. It then uses a large language model to generate a comprehensive answer based *only* on the most thoroughly vetted documents.

    Aegis mode represents the highest level of quality assurance in document selection, using advanced
    algorithms to meticulously evaluate document relevance before including them in the answer context.

    Use Cases:
    - Critical research questions where accuracy is paramount
    - Medical or scientific inquiries where precision is essential
    - Complex multi-faceted questions requiring the most relevant sources
    - When you need the highest confidence in the accuracy of citations
    - Situations where incorrect information could have serious consequences

    Trade-offs:
    - May be slower than Owl or Shield modes due to more thorough processing
    - Best used when quality matters more than speed

    Example: What are the molecular mechanisms of CRISPR-Cas9 gene editing and its current therapeutic applications?
    You could use this prompt passing query="What are the molecular mechanisms of CRISPR-Cas9 gene editing and its current therapeutic applications?"
    and langs=['en'], start_year=2020, end_year=-1, n=15.

    Args:
        query: The user's question.
        langs: The languages of the articles to retrieve. Default is ['en'].
        start_year: The start year for filtering articles. Default is -1 (no filter).
        end_year: The end year for filtering articles. Default is -1 (no filter).
        n: The number of articles to retrieve as context. Default is 10.

    Returns:
        A prompt with the question and the most carefully vetted context to answer the question.
    """
    logger.info(f"Received answer_aegis request with query: {query}, langs: {langs}, start_year: {start_year}, end_year: {end_year}, n: {n}")
    if start_year == -1:
        start_year = None
    if end_year == -1:
        end_year = None
    if langs == ['all'] or langs == ['All'] or langs == ['ALL']:
        langs = None
    async with httpx.AsyncClient(timeout=3600) as client:
        response = await client.post(
            f"{ASKAITHENA_API_URL}/answer-aegis",
            json={
                "query": query,
                "similarity_n": n,
                "languages": langs,
                "start_year": start_year,
                "end_year": end_year,
            },
        )
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    mcp.run(transport="http", port=3283, host="0.0.0.0")
