"""Example of how to use ollama to embed text.

It expects the ollama server to be running on localhost:11434.
"""

import json
import numpy as np
import requests


def test_embed_single():
    url = "http://localhost:11434/api/embed"
    payload = {"model": "nomic-embed-text", "input": "this is a test embedding"}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes
    result = response.json()["embeddings"][0]
    print(result)
    return result


def test_embed_batch():
    url = "http://localhost:11434/api/embed"
    payload = {
        "model": "nomic-embed-text",
        "input": ["this is a test embedding 1", "this is a test embedding 2"],
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes
    result = response.json()["embeddings"]
    res = np.array(result)
    print(res)
    return res
