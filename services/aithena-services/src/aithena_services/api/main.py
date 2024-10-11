# mypy: disable-error-code="import-untyped"
"""Aithena-Services FastAPI REST Endpoints. """

# pylint: disable=W1203, C0412, C0103, W0212

import json
from typing import Optional

import httpx
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from aithena_services.embeddings.azure_openai import AzureOpenAIEmbedding
from aithena_services.embeddings.ollama import OllamaEmbedding
from aithena_services.config import OLLAMA_HOST, TIMEOUT
from aithena_services.llms.azure_openai import AzureOpenAI
from aithena_services.llms.ollama import Ollama
from polus.aithena.common.logger import get_logger

logger = get_logger("aithena_services.api")


app = FastAPI()


def check_platform(platform: str):
    """Check if the platform is valid."""
    if platform not in ["ollama", "azure"]:
        logger.error(f"Invalid platform: {platform}")
        raise HTTPException(
            status_code=404,
            # detail="Invalid platform, must be 'ollama', 'openai' or 'azure'",
            detail="Invalid platform, must be 'ollama' or 'azure'",
        )


@app.get("/test")
def test():
    """Test FastAPI deployment."""
    logger.debug("Testing FastAPI deployment")
    return {"status": "success"}


@app.get("/chat/list")
def list_chat_models():
    """List all available chat models."""
    try:
        az = AzureOpenAI.list_models()
        ol = Ollama.list_models()
    except Exception as exc:
        logger.error(f"Error in listing chat models: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    return [*az, *ol]


@app.get("/chat/list/{platform}")
def list_chat_models_by_platform(platform: str):
    """List all available chat models by platform."""
    check_platform(platform)
    if platform == "azure":
        try:
            return AzureOpenAI.list_models()
        except Exception as exc:
            logger.error(f"Error in listing chat models in Azure: {exc}")
            raise HTTPException(status_code=400, detail=f"There was a problem listing chat models in Azure: {str(exc)}")
    try:
        return Ollama.list_models()
    except Exception as exc:
        logger.error(f"Error in listing chat models in Ollama: {exc}")
        raise HTTPException(status_code=400, detail=f"There was a problem listing chat models in Ollama: {str(exc)}")


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
        try:
            return AzureOpenAIEmbedding.list_models()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"There was a problem listing embed models in Azure: {str(exc)}")
    try:
        return OllamaEmbedding.list_models()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"There was a problem listing embed models in Ollama: {str(exc)}")

def resolve_client_chat(model: str, num_ctx: Optional[int]):
    """Resolve client for chat models."""
    if model in AzureOpenAI.list_models():
        try:
            return AzureOpenAI(deployment=model)
        except Exception as exc:
            logger.error(f"Error in resolving Azure client for model: {model}")
            raise HTTPException(status_code=400, detail=f"Error in resolving Azure chat client for model: {model}, {str(exc)}") 
    if f"{model}:latest" in Ollama.list_models():
        return resolve_client_chat(f"{model}:latest", num_ctx)
    if model in Ollama.list_models():
        try:
            if num_ctx:
                return Ollama(model=model, context_window=num_ctx, request_timeout=500)
        except Exception as exc:
            logger.error(f"Error in resolving Ollama client for model: {model}")
            raise HTTPException(status_code=400, detail=f"Error in resolving Ollama chat client for model: {model}, {str(exc)}")
        try:
            return Ollama(model=model)
        except Exception as exc:
            logger.error(f"Error in resolving Ollama client for model: {model}")
            raise HTTPException(status_code=400, detail=f"Error in resolving Ollama chat client for model: {model}, {str(exc)}")
    logger.error(f"Chat model not found: {model}")
    raise HTTPException(status_code=404, detail="Chat model not found.")


def resolve_client_embed(model: str):
    """Resolve client for embed models."""
    if model in AzureOpenAIEmbedding.list_models():
        try:
            return AzureOpenAIEmbedding(deployment=model)
        except Exception as exc:
            logger.error(f"Error in resolving Azure embed client for model: {model}")
            raise HTTPException(status_code=400, detail=f"Error in resolving Azure embed client for model: {model}, {str(exc)}")
    if f"{model}:latest" in OllamaEmbedding.list_models():
        try:
            return OllamaEmbedding(model=f"{model}:latest")
        except Exception as exc:
            logger.error(f"Error in resolving Ollama embed client for model: {model}")
            raise HTTPException(status_code=400, detail=f"Error in resolving Ollama embed client for model: {model}, {str(exc)}")
    if model in OllamaEmbedding.list_models():
        try:
            return OllamaEmbedding(model=model)
        except Exception as exc:
            logger.error(f"Error in resolving Ollama embed client for model: {model}")
            raise HTTPException(status_code=400, detail=f"Error in resolving Ollama embed client for model: {model}, {str(exc)}")
    logger.error(f"Embed model not found: {model}")
    raise HTTPException(status_code=404, detail="Embed model not found.")


@app.post("/chat/{model}/generate")
async def generate_from_msgs(
    model: str,
    messages: list[dict] | str,
    stream: bool = False,
    num_ctx: Optional[int] = None,
):
    """Generate a chat completion from a list of messages."""

    logger.debug(
        f"For {model} chat, received {messages}, stream: {stream}, num_ctx: {num_ctx}"
    )
    client = resolve_client_chat(model, num_ctx)

    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    if stream:

        async def stream_response(messages):
            try:
                async for chunk in await client.astream_chat(messages):
                    response = chunk.__dict__
                    response["message"] = chunk.message.as_json()
                    yield json.dumps(response, default=lambda x: x.model_dump_json()) + "\n"
            except httpx.ReadTimeout as exc:
                logger.error(f"Timeout error in chat stream response")
                yield json.dumps({"error": "Timeout error in chat stream response"}) + "\n"
                # raise HTTPException(status_code=408, detail="Timeout error in chat stream response")
            except Exception as exc:
                logger.error(f"Error in chat stream response: {str(exc)}")
                yield json.dumps({"error": f"Error in chat stream response: {str(exc)}"}) + "\n"

        return StreamingResponse(
            stream_response(messages), media_type="application/json"
        )
    try:
        res = await client.achat(messages)
        return res.as_json()
    except httpx.ReadTimeout as exc:
        logger.error(f"Timeout error in chat response")
        raise HTTPException(status_code=408, detail="Timeout error in chat response")
    except Exception as exc:
        logger.error(f"Error in chat generation: {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/embed/{model}/generate")
async def text_embeddings(
    model: str,
    text: str | list[str],
):
    """Get text embeddings."""
    client = resolve_client_embed(model)
    try:
        logger.info(f"Embedding with client: {client}")
        if isinstance(text, str):
            res = await client._aget_text_embedding(text)
        if isinstance(text, list):
            res = await client._aget_text_embeddings(text)
    except httpx.ReadTimeout as exc:
        logger.error(f"Timeout error in embedding generation")
        raise HTTPException(status_code=408, detail="Timeout error in embedding generation")
    except Exception as exc:
        logger.error(f"Error in text embeddings: {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc))
    return res


@app.post("/ollama/pull/{model}")
async def pull_ollama_model(model: str):
    """Pull Ollama model."""
    logger.debug(f"Pulling Ollama model: {model}")

    async def stream_response():
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                async with client.stream(
                    "POST", f"{OLLAMA_HOST}/api/pull", json={"name": model}
                ) as response:
                    async for line in response.aiter_lines():
                        yield line + "\n"
        except httpx.ReadTimeout as exc:
            logger.error(f"Timeout error in Ollama model pull")
            yield json.dumps({"error": "Timeout error in Ollama model pull"}) + "\n"
        except Exception as exc:
            logger.error(f"Error in chat Ollama model pull: {str(exc)}")
            yield json.dumps({"error": f"Error in Ollama model pull: {str(exc)}"}) + "\n"

    return StreamingResponse(stream_response(), media_type="application/json")


@app.get("/ollama/ps")
async def ollama_ps():
    """List Ollama models running."""
    logger.debug(f"Listing Ollama models running")
    try:
        res = httpx.get(f"{OLLAMA_HOST}/api/ps", timeout=TIMEOUT).json()
    except httpx.ReadTimeout as exc:
        logger.error(f"Timeout error in Ollama ps")
        raise HTTPException(status_code=408, detail="Timeout error in Ollama ps")
    except Exception as exc:
        logger.error(f"Error in Ollama ps: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    return res


@app.delete("/ollama/delete/{model}")
async def ollama_delete(model: str):
    """Delete Ollama model."""
    logger.debug(f"Deleting Ollama model: {model}")
    try:
        res = requests.delete(f"{OLLAMA_HOST}/api/delete", json={"name": model}, timeout=TIMEOUT)
        res.raise_for_status()
    except Exception as exc:
        logger.error(f"Error in deleting Ollama model: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "success"}
