# mypy: disable-error-code="import-untyped"
"""FastAPI Aithena Service Test Module."""

import json
import random

# pylint: disable=C0415, W0621, C0413, C0103
import pytest
import requests
from dotenv import find_dotenv, load_dotenv

from aithena_services.envvars import (
    AZURE_OPENAI_AVAILABLE,
    OLLAMA_AVAILABLE,
    OPENAI_AVAILABLE,
)

load_dotenv(find_dotenv(), override=True)

URL = "http://localhost:8000"

OLLAMA_LLAMA31_TEMPERATURE = {
    "name": "llama3.1-temp",
    "model": "llama3.1",
    "config": {"url": "http://localhost:11434"},
    "backend": "ollama",
    "params": {"temperature": 0.9},
}
DIRECT_GPT_4O_ADD = {
    "name": "testinggpt4o12",
    "model": "gpt-4o-mini",
    "backend": "openai",
    "config": {},
    "params": None,
}
EMBED_NOMIC_ADD = {
    "name": "testnomic12",
    "model": "nomic-embed-text",
    "backend": "ollama",
    "config": {},
    "params": None,
}


def test_update_chat_models():
    """Test update chat models from config."""
    res = requests.put(URL + "/chat/list/update", timeout=20).json()
    assert res == {"status": "success"}


def test_list_chat_models():
    """Test list models."""
    res = requests.get(URL + "/chat/list", timeout=20).json()
    assert isinstance(res, list)


def test_add_chat_model():
    """Test add chat model."""
    if DIRECT_GPT_4O_ADD["name"] in requests.get(URL + "/chat/list", timeout=20).json():
        DIRECT_GPT_4O_ADD["name"] = "testinggpt4o" + str(random.randint(1, 100))
    res = requests.post(
        URL + "/chat/list/add", json=DIRECT_GPT_4O_ADD, timeout=20
    ).json()
    assert res == {"status": "success"}


def test_delete_chat_model():
    """Test delete chat model."""
    if (
        DIRECT_GPT_4O_ADD["name"]
        not in requests.get(URL + "/chat/list", timeout=20).json()
    ):
        requests.post(URL + "/chat/list/add", json=DIRECT_GPT_4O_ADD, timeout=20)
    res = requests.delete(
        URL + "/chat/list/delete/testinggpt4o12", json=DIRECT_GPT_4O_ADD, timeout=20
    ).json()
    assert res == {"status": "success"}


def test_update_embed_models():
    """Test update embed models from config."""
    res = requests.put(URL + "/embed/list/update", timeout=20).json()
    assert res == {"status": "success"}


def test_list_embed_models():
    """Test list embed models."""
    res = requests.get(URL + "/embed/list", timeout=20).json()
    assert isinstance(res, list)


def test_add_embed_model():
    """Test add embed model."""
    if EMBED_NOMIC_ADD["name"] in requests.get(URL + "/embed/list", timeout=20).json():
        EMBED_NOMIC_ADD["name"] = "testnomic12" + str(random.randint(1, 100))
    res = requests.post(
        URL + "/embed/list/add", json=EMBED_NOMIC_ADD, timeout=20
    ).json()
    assert res == {"status": "success"}


def test_delete_embed_model():
    """Test delete embed model."""
    if (
        EMBED_NOMIC_ADD["name"]
        not in requests.get(URL + "/embed/list", timeout=20).json()
    ):
        requests.post(URL + "/embed/list/add", json=EMBED_NOMIC_ADD, timeout=20)
    res = requests.delete(
        URL + "/embed/list/delete/testnomic12", json=EMBED_NOMIC_ADD, timeout=20
    ).json()
    assert res == {"status": "success"}


def test_stream_chat_1(math_question):
    """Test stream chat 1."""
    models = requests.get(URL + "/chat/list", timeout=20).json()
    if "llama3.1:latest" in models:
        model = "llama3.1:latest"
    else:
        model = models[0]
    res = requests.post(
        URL + f"/chat/{model}/generate", json=math_question, timeout=20, stream=True
    )
    for msg in res.iter_lines():
        msg_json = json.loads(msg)
        assert "message" in msg_json
        assert "delta" in msg_json
        assert isinstance(msg_json["delta"], str)


def test_chat_1(math_question):
    """Test chat no stream 1."""
    models = requests.get(URL + "/chat/list", timeout=20).json()
    if "llama3.1:latest" in models:
        model = "llama3.1:latest"
    else:
        model = models[0]
    res = requests.post(
        URL + f"/chat/{model}/generate",
        json=math_question,
        timeout=20,
        stream=False,
        params={"stream": False},
    ).json()
    assert "message" in res
    assert isinstance(res["message"]["content"], str)


@pytest.mark.skipif(not AZURE_OPENAI_AVAILABLE, reason="azure not available")
def test_azure_chat(math_question):
    """Test azure chat."""
    if len(requests.get(URL + "/chat/list/azure", timeout=20).json()) == 0:
        pytest.skip("No azure models available")
    model_ = requests.get(URL + "/chat/list/azure", timeout=20).json()[0]
    res = requests.post(
        URL + f"/chat/{model_}/generate",
        json=math_question,
        timeout=20,
        stream=False,
        params={"stream": False},
    ).json()
    assert "message" in res
    assert isinstance(res["message"]["content"], str)


@pytest.mark.skipif(not AZURE_OPENAI_AVAILABLE, reason="azure not available")
def test_azure_stream_chat(math_question):
    """Test azure stream chat."""
    if len(requests.get(URL + "/chat/list/azure", timeout=20).json()) == 0:
        pytest.skip("No azure models available")
    model_ = requests.get(URL + "/chat/list/azure", timeout=20).json()[0]
    res = requests.post(
        URL + f"/chat/{model_}/generate", json=math_question, timeout=20, stream=True
    )
    for msg in res.iter_lines():
        msg_json = json.loads(msg)
        assert "message" in msg_json
        assert "delta" in msg_json
        assert isinstance(msg_json["delta"], str)


@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="ollama not available")
def test_ollama_chat(math_question):
    """Test Ollama chat."""
    if len(requests.get(URL + "/chat/list/ollama", timeout=20).json()) == 0:
        pytest.skip("No ollama models available")
    models = requests.get(URL + "/chat/list/ollama", timeout=20).json()
    if "llama3.1:latest" in models:
        model_ = "llama3.1:latest"
    else:
        model_ = models[0]
    res = requests.post(
        URL + f"/chat/{model_}/generate",
        json=math_question,
        timeout=20,
        stream=False,
        params={"stream": False},
    ).json()
    assert "message" in res
    assert isinstance(res["message"]["content"], str)


@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="ollama not available")
def test_ollama_stream_chat(math_question):
    """Test Ollama stream chat."""
    if len(requests.get(URL + "/chat/list/ollama", timeout=20).json()) == 0:
        pytest.skip("No ollama models available")
    models = requests.get(URL + "/chat/list/ollama", timeout=20).json()
    if "llama3.1:latest" in models:
        model_ = "llama3.1:latest"
    else:
        model_ = models[0]
    res = requests.post(
        URL + f"/chat/{model_}/generate", json=math_question, timeout=20, stream=True
    )
    for msg in res.iter_lines():
        msg_json = json.loads(msg)
        assert "message" in msg_json
        assert "delta" in msg_json
        assert isinstance(msg_json["delta"], str)


@pytest.mark.skipif(not OPENAI_AVAILABLE, reason="openai not available")
def test_openai_chat(math_question):
    """Test OpenAI chat."""
    if len(requests.get(URL + "/chat/list/openai", timeout=20).json()) == 0:
        pytest.skip("No openai models available")
    model_ = requests.get(URL + "/chat/list/openai", timeout=20).json()[0]
    res = requests.post(
        URL + f"/chat/{model_}/generate",
        json=math_question,
        timeout=20,
        stream=False,
        params={"stream": False},
    ).json()
    assert "message" in res
    assert isinstance(res["message"]["content"], str)


@pytest.mark.skipif(not OPENAI_AVAILABLE, reason="openai not available")
def test_openai_stream_chat(math_question):
    """Test openai stream chat."""
    if len(requests.get(URL + "/chat/list/openai", timeout=20).json()) == 0:
        pytest.skip("No openai models available")
    model_ = requests.get(URL + "/chat/list/openai", timeout=20).json()[0]
    res = requests.post(
        URL + f"/chat/{model_}/generate", json=math_question, timeout=20, stream=True
    )
    for msg in res.iter_lines():
        msg_json = json.loads(msg)
        assert "message" in msg_json
        assert "delta" in msg_json
        assert isinstance(msg_json["delta"], str)


@pytest.mark.skipif(not AZURE_OPENAI_AVAILABLE, reason="azure not available")
def test_azure_embed_str():
    """Test azure embed."""
    if len(requests.get(URL + "/embed/list/azure", timeout=20).json()) == 0:
        pytest.skip("No azure models available")
    model_ = requests.get(URL + "/embed/list/azure", timeout=20).json()[0]
    res = requests.post(
        URL + f"/embed/{model_}/generate",
        json="This is a test",
        timeout=20,
        stream=False,
    ).json()
    assert isinstance(res, list)
    assert isinstance(res[0], float)


@pytest.mark.skipif(not AZURE_OPENAI_AVAILABLE, reason="azure not available")
def test_azure_embed_list():
    """Test azure embed list."""
    if len(requests.get(URL + "/embed/list/azure", timeout=20).json()) == 0:
        pytest.skip("No azure models available")
    model_ = requests.get(URL + "/embed/list/azure", timeout=20).json()[0]
    res = requests.post(
        URL + f"/embed/{model_}/generate",
        json=["This is a test", "This is another test"],
        timeout=20,
        stream=False,
    ).json()
    assert isinstance(res, list)
    assert isinstance(res[0], list)
    assert isinstance(res[0][0], float)


@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="ollama not available")
def test_ollama_embed_st():
    """Test ollama embed."""
    if len(requests.get(URL + "/embed/list/ollama", timeout=20).json()) == 0:
        pytest.skip("No ollama models available")
    model_ = requests.get(URL + "/embed/list/ollama", timeout=20).json()[0]
    res = requests.post(
        URL + f"/embed/{model_}/generate",
        json="This is a test",
        timeout=20,
        stream=False,
    ).json()
    assert isinstance(res, list)
    assert isinstance(res[0], float)


@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="ollama not available")
def test_ollama_embed_list():
    """Test ollama embed list."""
    if len(requests.get(URL + "/embed/list/ollama", timeout=20).json()) == 0:
        pytest.skip("No ollama models available")
    model_ = requests.get(URL + "/embed/list/ollama", timeout=20).json()[0]
    res = requests.post(
        URL + f"/embed/{model_}/generate",
        json=["This is a test", "This is another test"],
        timeout=20,
        stream=False,
    ).json()
    assert isinstance(res, list)
    assert isinstance(res[0], list)
    assert isinstance(res[0][0], float)
