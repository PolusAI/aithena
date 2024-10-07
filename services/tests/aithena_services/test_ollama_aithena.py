# mypy: disable-error-code="import-untyped"
"""Ollama Aithena Service Test Module."""

# pylint: disable=C0415, W0621, C0413, C0103
import pytest
import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)
from llama_index.core.base.llms.types import CompletionResponse
from llama_index.core.llms import ChatMessage

# this is after dotenv in case .env for tests
# defines different values for these variables
from aithena_services.envvars import OLLAMA_AVAILABLE, OLLAMA_HOST
from aithena_services.llms.types import ChatResponse, Message


def test_ollama_available():
    """Test OllamaAvailable from Aithena Services."""
    ol_av = OLLAMA_HOST is not None
    assert OLLAMA_AVAILABLE == ol_av


@pytest.fixture
def ollama_chat():
    """Return Ollama object from Aithena Services."""
    if not OLLAMA_AVAILABLE:
        pytest.skip("Ollama not available")
    from aithena_services.llms.ollama import Ollama

    if not "llama3.1:latest" in Ollama.list_models():
        raise ValueError("llama3.1 not available")

    return Ollama


@pytest.fixture
def ollama_embed():
    """Return Ollama object from Aithena Services."""
    if not OLLAMA_AVAILABLE:
        pytest.skip("Ollama not available")
    from aithena_services.embeddings.ollama import OllamaEmbedding

    if not "nomic-embed-text:latest" in OllamaEmbedding.list_models():
        raise ValueError("nomic-embed-text not available")

    return OllamaEmbedding


def test_ollama_list_chat_models(ollama_chat):
    """Test Aithena Services Ollama List Chat Models."""

    Ollama = ollama_chat
    req = requests.get(OLLAMA_HOST + "/api/tags", timeout=40).json()["models"]
    names_req = [x["name"] for x in req if "embed" not in x["name"]]
    names_obj = Ollama.list_models()
    assert names_req == names_obj


def test_ollama_list_embed_models(ollama_embed):
    """Test Aithena Services Ollama List Chat Models."""

    Ollama = ollama_embed
    req = requests.get(OLLAMA_HOST + "/api/tags", timeout=40).json()["models"]
    names_req = [x["name"] for x in req if "embed" in x["name"]]
    names_obj = Ollama.list_models()
    assert names_req == names_obj


def test_ollama_llama31_response_message(ollama_chat, math_question):
    """Test Aithena Services Ollama Llama3.1.

    Test response contains Message.
    """
    Ollama = ollama_chat
    llama = Ollama(model="llama3.1")
    response = llama.chat(math_question)
    assert isinstance(response.message, Message)


def test_ollama_llama31_response_message_content(ollama_chat, math_question):
    """Test Aithena Services Ollama Llama3.1.

    Test response contains Message.
    """
    Ollama = ollama_chat
    llama = Ollama(model="llama3.1")
    response = llama.chat(math_question)
    assert isinstance(response.message.content, str)


def test_ollama_llama31_response(ollama_chat, math_question):
    """Test Aithena Services Ollama Llama3.1.

    Test response object.
    """
    Ollama = ollama_chat
    llama = Ollama(model="llama3.1")
    response = llama.chat(math_question)
    assert isinstance(response, ChatResponse)


def test_ollama_llama31_vs_llamaindex(ollama_chat, math_question):
    """Test Aithena Services Ollama Llama3.1.

    Test response object of Aithena vs LlamaIndex.
    """
    from llama_index.core.llms import ChatMessage
    from llama_index.llms.ollama import Ollama as LlamaIndexOllama

    Ollama = ollama_chat
    llama = Ollama(model="llama3.1")
    response = llama.chat(math_question)
    llama2 = LlamaIndexOllama(model="llama3.1")
    response2 = llama2.chat([ChatMessage(**x) for x in math_question])
    assert isinstance(response.message, Message)
    assert isinstance(response2.message, ChatMessage)
    for arg in response2.__dict__:
        if arg == "message":
            assert (
                getattr(response, arg).content.__class__
                == getattr(response2, arg).content.__class__
            )
        else:
            assert getattr(response, arg).__class__ == getattr(response2, arg).__class__


def test_ollama_llama31_stream_story(ollama_chat, text_question_1):
    """Test Aithena Services Ollama Llama3.1.

    Test response object in stream chat.
    """
    Ollama = ollama_chat
    llama = Ollama(model="llama3.1")
    response = llama.stream_chat(text_question_1)
    for r in response:
        assert isinstance(r, ChatResponse)
        assert isinstance(r.message, Message)
        assert isinstance(r.message.content, str)
        assert isinstance(r.delta, str)


def test_ollama_llama31_args1(ollama_chat, text_question_1):
    """Test Aithena Services Ollama Llama3.1.

    Test response with specific params with two instances
    of Aithena Services Ollama Llama3.1.
    """
    Ollama = ollama_chat
    llama = Ollama(model="llama3.1", temperature=0, seed=82)
    response1 = llama.chat(text_question_1)
    llama2 = Ollama(model="llama3.1", temperature=0, seed=82)
    response2 = llama2.chat(text_question_1)
    assert response1.message == response2.message


def test_ollama_llama31_args2(ollama_chat, query_1):
    """Test Aithena Services Ollama Llama3.1.

    Test response with specific params with Aithena
    vs REST API.
    """
    Ollama = ollama_chat
    llama = Ollama(model="llama3.1", temperature=0, seed=12)
    response1 = llama.chat(query_1)
    data = {
        "model": "llama3.1",
        "messages": [x.as_json() for x in query_1],
        "options": {"seed": 12, "temperature": 0},
        "stream": False,
    }
    response2 = requests.post(OLLAMA_HOST + "/api/chat", json=data, timeout=40).json()[
        "message"
    ]["content"]

    assert response1.message.content == response2


def test_ollama_llama31_args3(ollama_chat, query_1):
    """Test Aithena Services Ollama Llama3.1.

    Test response with specific params with Aithena
    vs LlamaIndex.
    """
    from llama_index.core.llms import ChatMessage
    from llama_index.llms.ollama import Ollama as LlamaIndexOllama

    Ollama = ollama_chat
    llama = Ollama(model="llama3.1", temperature=0, seed=12)
    response1 = llama.chat(query_1)
    response2 = LlamaIndexOllama(model="llama3.1", temperature=0, seed=12).chat(
        [ChatMessage(**x.as_json()) for x in query_1]
    )

    assert response1.message.content == response2.message.content


@pytest.mark.asyncio(scope="session")
async def test_chat_async_stream(ollama_chat):
    """Async stream implementation of ollama chat integration."""
    Ollama = ollama_chat
    llama = Ollama(model="llama3.1", temperature=0, seed=12)
    messages = [ChatMessage(**{"role": "user", "content": "Hi there!"})]
    chunks = await llama.astream_chat(messages)
    async for chunk in chunks:  # NOTE the async for iterating the async generator
        print(chunk.delta, end="", flush=True)
        # logger.info(f"output: {chunk.message.content}")


def test_ollama_completion(ollama_chat):
    """Test completion in Ollama."""
    Ollama = ollama_chat
    llama = Ollama(model="llama3.1", temperature=0, seed=12)
    response = llama.complete("What is the capital of France?")
    assert isinstance(response, CompletionResponse)
    assert isinstance(response.text, str)


def test_ollama_completion_stream(ollama_chat):
    """Test completion stream in Ollama."""
    Ollama = ollama_chat
    llama = Ollama(model="llama3.1", temperature=0, seed=12)
    response = llama.stream_complete("What is the capital of France?")
    for r in response:
        assert isinstance(r, CompletionResponse)
        assert isinstance(r.text, str)
        assert isinstance(r.delta, str)


def test_ollama_embedding_text(ollama_embed):
    """Test text embeddings in Ollama."""
    OllamaEmbedding = ollama_embed
    ollama = OllamaEmbedding(model="nomic-embed-text")
    response = ollama.get_text_embedding("What is the capital of France?")
    assert isinstance(response, list)
    assert isinstance(response[0], float)


def test_ollama_embedding_batch(ollama_embed):
    """Test batch text embeddings in Ollama."""
    OllamaEmbedding = ollama_embed
    ollama = OllamaEmbedding(model="nomic-embed-text")
    response = ollama.get_text_embedding_batch(
        [
            "What is the capital of France?",
            "What is the capital of Germany?",
            "What is the capital of Colombia?",
        ]
    )
    assert isinstance(response, list)
    assert isinstance(response[0], list)
    assert isinstance(response[0][0], float)
    assert isinstance(response[1], list)
    assert isinstance(response[1][2], float)
    assert isinstance(response[2], list)
    assert isinstance(response[2][4], float)
