# mypy: disable-error-code="import-untyped"
"""Aithena-Services FastAPI REST Endpoints. """

# pylint: disable=W1203, C0412, C0103, W0212

import json
from logging import getLogger

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from aithena_services.embeddings.azure_openai import AzureOpenAIEmbedding
from aithena_services.embeddings.ollama import OllamaEmbedding
from aithena_services.llms.azure_openai import AzureOpenAI
from aithena_services.llms.ollama import Ollama
from aithena_services.envvars import OLLAMA_HOST
import requests
import httpx

logger = getLogger(__name__)


app = FastAPI()


def check_platform(platform: str):
    """Check if the platform is valid."""
    if platform not in ["ollama", "azure"]:
        raise HTTPException(
            status_code=400,
            # detail="Invalid platform, must be 'ollama', 'openai' or 'azure'",
            detail="Invalid platform, must be 'ollama' or 'azure'",
        )


@app.get("/test")
def test():
    """Test FastAPI deployment."""
    return {"status": "success"}


@app.get("/chat/list")
def list_chat_models():
    """List all available chat models."""
    try:
        az = AzureOpenAI.list_models()
        ol = Ollama.list_models()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [*az, *ol]


@app.get("/chat/list/{platform}")
def list_chat_models_by_platform(platform: str):
    """List all available chat models by platform."""
    check_platform(platform)
    if platform == "azure":
        try:
            return AzureOpenAI.list_models()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        return Ollama.list_models()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/embed/list")
def list_embed_models():
    """List all available embed models."""
    az = AzureOpenAIEmbedding.list_models()
    ol = OllamaEmbedding.list_models()
    return [*az, *ol]


@app.get("/embed/list/{platform}")
def list_embed_models_by_platform(platform: str):
    """List all available embed models by platform."""
    check_platform(platform)
    if platform == "azure":
        return AzureOpenAIEmbedding.list_models()
    return OllamaEmbedding.list_models()


def resolve_client_chat(model: str):
    """Resolve client for chat models."""
    if model in AzureOpenAI.list_models():
        return AzureOpenAI(deployment=model)
    if f"{model}:latest" in Ollama.list_models():
        return Ollama(model=f"{model}:latest")
    if model in Ollama.list_models():
        return Ollama(model=model)
    raise HTTPException(status_code=400, detail="Invalid model.")


def resolve_client_embed(model: str):
    """Resolve client for embed models."""
    if model in AzureOpenAIEmbedding.list_models():
        return AzureOpenAIEmbedding(deployment=model)
    if f"{model}:latest" in OllamaEmbedding.list_models():
        return OllamaEmbedding(model=f"{model}:latest")
    if model in OllamaEmbedding.list_models():
        return OllamaEmbedding(model=model)
    raise HTTPException(status_code=400, detail="Invalid model.")


@app.post("/chat/{model}/generate")
async def generate_from_msgs(
    model: str,
    messages: list[dict] | str,
    stream: bool = False,
):
    """Generate a chat completion from a list of messages."""

    print(f"For {model} chat, received {messages}, stream: {stream}")
    client = resolve_client_chat(model)

    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    if stream:

        async def stream_response(messages):
            async for chunk in await client.astream_chat(messages):
                response = chunk.__dict__
                response["message"] = chunk.message.as_json()
                yield json.dumps(response, default=lambda x: x.model_dump_json()) + "\n"

        return StreamingResponse(
            stream_response(messages), media_type="application/json"
        )
    try:
        res = await client.achat(messages)
    except Exception as exc:
        logger.error(f"Error in chat generation: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return res.as_json()


@app.post("/embed/{model}/generate")
async def text_embeddings(
    model: str,
    text: str | list[str],
):
    """Get text embeddings."""
    client = resolve_client_embed(model)
    try:
        print(f"Embedding with client: {client}")
        if isinstance(text, str):
            res = await client._aget_text_embedding(text)
        if isinstance(text, list):
            res = await client._aget_text_embeddings(text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return res

@app.post("/ollama/pull/{model}")
async def pull_ollama_model(model: str):
    """Pull Ollama model."""
    try:
        async def stream_response():
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST", f"{OLLAMA_HOST}/api/pull", json={"name": model}
                ) as response:
                    async for line in response.aiter_lines():
                        yield line + "\n"

        return StreamingResponse(
            stream_response(), media_type="application/json"
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/ollama/ps")
async def ollama_ps():
    """List Ollama models running."""
    try:
        res = httpx.get(f"{OLLAMA_HOST}/api/ps").json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return res

@app.delete("/ollama/delete/{model}")
async def ollama_delete(model: str):
    """Delete Ollama model."""
    try:
        res = requests.delete(f"{OLLAMA_HOST}/api/delete", json={"name": model})
        res.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success"}
