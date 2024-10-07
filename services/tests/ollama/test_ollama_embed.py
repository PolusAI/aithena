"""Demonstrate ollama embeddings capabilities.
"""

import ollama

def test_embed():
    resp = ollama.embeddings(model='llama3.1', prompt='The sky is blue because of rayleigh scattering')
    assert len(resp["embedding"]) == 4096