import json
import httpx
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from polus.aithena.common.logger import get_logger
from polus.aithena.ask_aithena import (
    AskAithenaQuery,
    AskAithenaResponse,
    ask,
    ask_stream,
    config,
)


logger = get_logger(__file__)
app = FastAPI()


@app.get("/")
async def status():
    return {"status": "ask-aithena agent is running"}


@app.post("/ask", response_model=AskAithenaResponse)
async def ask_aithena(query: AskAithenaQuery, stream: bool = False):
    logger.debug(f"ask aithena received a query: {query}")
    if not stream:
        return ask(query)
    else:
        url = config.AITHENA_SERVICE_URL + f"/chat/{config.CHAT_MODEL}/generate"
        msgs, refs = ask_stream(query)

        # move to ask stream?
        async def stream_generator():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST", url, json=msgs, params={"stream": True}
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            yield line + "\n"
                    yield json.dumps({"delta": refs}) + "\n"  # delta is for dashboard

        return StreamingResponse(stream_generator(), media_type="application/json")
