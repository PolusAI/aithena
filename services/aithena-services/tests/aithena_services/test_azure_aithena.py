# mypy: disable-error-code="import-untyped"
"""Azure Aithena Service Test Module."""

# pylint: disable=C0415, W0621, C0413, C0103
import os
from difflib import SequenceMatcher

import pytest
import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)
from llama_index.core.base.llms.types import CompletionResponse

# this is after dotenv in case .env for tests
# defines different values for these variables
from aithena_services.envvars import AZURE_OPENAI_AVAILABLE, AZURE_OPENAI_ENV_DICT
from aithena_services.llms.types import ChatResponse, Message

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
MODEL = os.getenv("AZURE_OPENAI_MODEL")


def test_azure_available():
    """Test AZURE_OPENAI_AVAILABLE from Aithena Services."""
    az_av = (
        AZURE_OPENAI_ENV_DICT["api_key"] is not None
        and AZURE_OPENAI_ENV_DICT["azure_endpoint"] is not None
        and AZURE_OPENAI_ENV_DICT["api_version"] is not None
    )
    assert AZURE_OPENAI_AVAILABLE == az_av


@pytest.fixture
def azure_chat():
    """Return azure chat object from Aithena Services."""
    if not AZURE_OPENAI_AVAILABLE:
        pytest.skip("azure not available")
    from aithena_services.llms.azure_openai import AzureOpenAI  # type: ignore

    return AzureOpenAI


@pytest.fixture
def azure_embed():
    """Return azure embed object from Aithena Services."""
    if not AZURE_OPENAI_AVAILABLE:
        pytest.skip("azure not available")
    from aithena_services.embeddings.azure_openai import (
        AzureOpenAIEmbedding,  # type: ignore
    )

    return AzureOpenAIEmbedding


def test_azure_response_message(azure_chat, math_question):
    """Test Aithena Services azure.

    Test response contains Message.
    """
    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT)
    response = gpt4o.chat(math_question)
    assert isinstance(response.message, Message)


def test_azure_response_message_content(azure_chat, math_question):
    """Test Aithena Services azure.

    Test response contains Message.
    """
    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT)
    response = gpt4o.chat(math_question)
    assert isinstance(response.message.content, str)


def test_azure_response(azure_chat, math_question):
    """Test Aithena Services azure.

    Test response object.
    """
    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT)
    response = gpt4o.chat(math_question)
    assert isinstance(response, ChatResponse)


def test_azure_vs_llamaindex(azure_chat, math_question):
    """Test Aithena Services azure.

    Test response object of Aithena vs LlamaIndex.
    """
    from llama_index.core.llms import ChatMessage
    from llama_index.llms.azure_openai import AzureOpenAI as LlamaIndexAzureOpenAI

    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT)
    response = gpt4o.chat(math_question)
    gpt4o2 = LlamaIndexAzureOpenAI(
        model=MODEL,
        engine=DEPLOYMENT,
        api_key=AZURE_OPENAI_ENV_DICT["api_key"],
        azure_endpoint=AZURE_OPENAI_ENV_DICT["azure_endpoint"],
        api_version=AZURE_OPENAI_ENV_DICT["api_version"],
    )
    response2 = gpt4o2.chat([ChatMessage(**x) for x in math_question])
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


def test_azure_stream_story(azure_chat, text_question_1):
    """Test Aithena Services azure.

    Test response object in stream chat.
    """
    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT)
    response = gpt4o.stream_chat(text_question_1)
    for r in response:
        assert isinstance(r, ChatResponse)
        assert isinstance(r.message, Message)
        assert isinstance(r.message.content, str)
        assert isinstance(r.delta, str)


def test_azure_args1(azure_chat, text_question_1):
    """Test Aithena Services azure.

    Test response with specific params with two instances
    of Aithena Services azure.
    """
    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT, temperature=0, seed=45)
    response1 = gpt4o.chat(text_question_1)
    gpt4o2 = azure(model=MODEL, deployment=DEPLOYMENT, temperature=0, seed=45)
    response2 = gpt4o2.chat(text_question_1)
    ratio1 = SequenceMatcher(
        None, response1.message.content, response2.message.content
    ).ratio()
    gpt4o3 = azure(model=MODEL, deployment=DEPLOYMENT, temperature=0.9, seed=45)
    response3 = gpt4o3.chat(text_question_1)
    ratio2 = SequenceMatcher(
        None, response1.message.content, response3.message.content
    ).ratio()
    assert ratio1 > ratio2


def test_azure_args2(azure_chat, query_1):
    """Test Aithena Services azure.

    Test response with specific params with Aithena
    vs REST API.
    """
    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT, temperature=0, seed=12)
    response1 = gpt4o.chat(query_1)
    url = f"""
    {AZURE_OPENAI_ENV_DICT["azure_endpoint"]}openai/
    deployments/{DEPLOYMENT}/chat/
    completions?api-version={AZURE_OPENAI_ENV_DICT["api_version"]}
    """.replace(
        "\n", ""
    ).replace(
        " ", ""
    )
    headers = {
        "api-key": AZURE_OPENAI_ENV_DICT["api_key"],
    }
    data = {
        "messages": [x.as_json() for x in query_1],
        "temperature": 0,
        "seed": 12,
    }
    response2 = requests.post(url, headers=headers, json=data, timeout=40).json()[
        "choices"
    ][0]

    ratio1 = SequenceMatcher(
        None, response1.message.content, response2["message"]["content"]
    ).ratio()
    response3 = azure(
        model=MODEL, deployment=DEPLOYMENT, temperature=1.556, seed=12
    ).chat(query_1)
    ratio2 = SequenceMatcher(
        None, response1.message.content, response3.message.content
    ).ratio()
    print(ratio1, ratio2)
    assert ratio1 > ratio2


def test_azure_args3(azure_chat, query_1):
    """Test Aithena Services Azure.

    Test response with specific params with Aithena
    vs LlamaIndex.
    """
    from llama_index.core.llms import ChatMessage
    from llama_index.llms.azure_openai import AzureOpenAI as LlamaIndexAzureOpenAI

    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT, temperature=0, seed=12)
    response1 = gpt4o.chat(query_1)
    gpt4o2 = LlamaIndexAzureOpenAI(
        model=MODEL,
        engine=DEPLOYMENT,
        api_key=AZURE_OPENAI_ENV_DICT["api_key"],
        azure_endpoint=AZURE_OPENAI_ENV_DICT["azure_endpoint"],
        api_version=AZURE_OPENAI_ENV_DICT["api_version"],
        temperature=0,
        seed=12,
    )
    response2 = gpt4o2.chat([ChatMessage(**x.as_json()) for x in query_1])
    gpt4o3 = LlamaIndexAzureOpenAI(
        model=MODEL,
        engine=DEPLOYMENT,
        api_key=AZURE_OPENAI_ENV_DICT["api_key"],
        azure_endpoint=AZURE_OPENAI_ENV_DICT["azure_endpoint"],
        api_version=AZURE_OPENAI_ENV_DICT["api_version"],
        temperature=0.89,
        seed=18,
    )
    response3 = gpt4o3.chat([ChatMessage(**x.as_json()) for x in query_1])
    ratio1 = SequenceMatcher(
        None, response1.message.content, response2.message.content
    ).ratio()
    ratio2 = SequenceMatcher(
        None, response1.message.content, response3.message.content
    ).ratio()
    print(ratio1, ratio2)
    assert ratio1 > ratio2


def test_azure_deployment_arg(azure_chat):
    """Test the deployment argument in AzureOpenAI."""
    azure = azure_chat
    gpt4o1 = azure(model=MODEL, deployment=DEPLOYMENT)
    gpt4o2 = azure(model=MODEL, engine=DEPLOYMENT)
    assert gpt4o1.engine == gpt4o2.engine


def test_azure_completion(azure_chat):
    """Test completion in AzureOpenAI."""
    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT)
    response = gpt4o.complete("What is the capital of France?")
    assert isinstance(response, CompletionResponse)
    assert isinstance(response.text, str)


def test_azure_completion_stream(azure_chat):
    """Test completion stream in AzureOpenAI."""
    azure = azure_chat
    gpt4o = azure(model=MODEL, deployment=DEPLOYMENT)
    response = gpt4o.stream_complete("What is the capital of France?")
    for r in response:
        assert isinstance(r, CompletionResponse)
        assert isinstance(r.text, str)
        assert isinstance(r.delta, str)


def test_azure_embedding_text(azure_embed):
    """Test text embeddings in Azure."""
    azure = azure_embed(deployment="text-embedding-3-large")
    response = azure.get_text_embedding("What is the capital of France?")
    assert isinstance(response, list)
    assert isinstance(response[0], float)


def test_azure_embedding_batch(azure_embed):
    """Test batch text embeddings in Azure."""
    azure = azure_embed(deployment="text-embedding-3-large")
    response = azure.get_text_embedding_batch(
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
