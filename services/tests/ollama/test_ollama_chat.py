"""Test and benchmark ollama chat capabilities.

ollama chat options are listed here: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion

TODO we may want to demonstrate use of images (with multimodal models) and tools.
"""
from pathlib import Path
import ollama
import pytest
import numpy as np
import logging
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

"""Document params required to set up the client."""
host = os.getenv("OLLAMA_HOST", "") # this is what the ollama client expects
if host == "":
    host = os.getenv("OLLAMA_URL", "")


logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger(__file__)

logger.info(f"attempt to connect to ollama at: {host}")

# create a single client
async_client = ollama.AsyncClient(host)
client = ollama.Client(host)

RUN_COUNT = 1
PERF_LOGFILE = Path("perf.log")

# for visual debugging
# STREAM_END_TOKEN = "\n"
STREAM_END_TOKEN = ""
STREAM_FLUSH = False # if set to True force flush the stream if stream does not ends with "/n"

logger.info(f"using ollama at: {async_client._client._base_url}")

async def async_chat(messages):
    """Async chat."""
    try:
        async for resp_chunk in await async_client.chat(model='llama3.1', messages=messages, stream=True):
            print(resp_chunk['message']['content'], end=STREAM_END_TOKEN, flush=STREAM_FLUSH)
        return resp_chunk
    except ollama.ResponseError as e:
        logger.error("Ollama error", exc_info=True)
        raise


def chat(messages, stream=False):
    """Chat."""
    try:
        if stream:
            resp_chunks = client.chat(model='llama3.1', messages=messages, stream=stream)
            for chunk in resp_chunks:
                print(chunk['message']['content'], end=STREAM_END_TOKEN, flush=STREAM_FLUSH)
            return chunk
        
        resp = client.chat(model='llama3.1', messages=messages, stream=stream)
        logger.info(resp)
        return resp
    except ollama.ResponseError as e:
        logger.info('Error:', e.error)


@pytest.mark.asyncio
async def test_chat(user_message):
    """Test async chat."""
    total_durations = []
    for i in range(RUN_COUNT):
        messages = [user_message]
        res = await async_chat(messages)
        logger.info(res)
        assert res["done"] and res["done_reason"] == "stop"
        log_stats(res)
        total_durations.append(res["total_duration"])
    avg_total_duration = np.mean(np.array(total_durations)) * 10**-9
    with PERF_LOGFILE.open("a+") as fw:
        fw.write(f"async:True, stream:True, avg_total_duration: {avg_total_duration}s \n")


def test_chat_sync_stream(user_message):
    """Test synchronous chat as a stream."""
    total_durations = []
    for i in range(RUN_COUNT):
        messages = [user_message]
        res = chat(messages, stream=True)
        logger.info(res)
        assert res["done"] and res["done_reason"] == "stop"
        log_stats(res)
        total_durations.append(res["total_duration"])
    avg_total_duration = np.mean(np.array(total_durations)) * 10**-9
    with PERF_LOGFILE.open("a+") as fw:
        fw.write(f"async:False, stream:True, avg_total_duration: {avg_total_duration}s \n")


def test_chat_sync(user_message):
    """Test synchronous chat."""
    total_durations = []
    for i in range(RUN_COUNT):
        messages = [user_message]
        res = chat(messages, stream=False)
        logger.info(res)
        assert res["done"] and res["done_reason"] == "stop"
        log_stats(res)
        total_durations.append(res["total_duration"])
    avg_total_duration = np.mean(np.array(total_durations)) * 10**-9
    with PERF_LOGFILE.open("a+") as fw:
        fw.write(f"async:False, stream:False, avg_total_duration: {avg_total_duration}s \n")


def log_stats(res):
    token_per_second = res["eval_count"] / res["eval_duration"] * 10**9
    total_duration = res["total_duration"] / 10**9
    load_duration = res["load_duration"] / 10**9
    prompt_eval_duration = res["prompt_eval_duration"] / 10**9
    eval_duration = res["eval_duration"] / 10**9
    logger.info(f"token per second: {token_per_second}")
    logger.info(f"total duration: {total_duration}")
    logger.info(f"load duration: {load_duration}")
    logger.info(f"prompt eval duration: {prompt_eval_duration}")
    logger.info(f"eval duration: {eval_duration}")

