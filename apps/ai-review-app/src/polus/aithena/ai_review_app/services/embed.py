import json
import requests
from polus.aithena.common.logger import get_logger

logger = get_logger(__file__)

class IncorrectEmbeddingDimensionsError(Exception):
    """Exception raised when embeddings have incorrect dimensions."""

class EmbeddingServiceOllama:

    """Embedding service using Ollama."""
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.embed_url= endpoint + "/api/embed"
        self.healthcheck_url= endpoint + "/api/tags"

    def healthcheck(self) -> bool:
        requests.get(self.healthcheck_url)

    def embed_all(self, instruct_queries: list[tuple[str,str]], batch_size: int = 1 ) -> requests.Response:
        """Embed data.
        
        The signature convert to old convert service for compatiblity.
        """
        docs = [q[1] for q in instruct_queries]
        payload = {"model": "nomic-embed-text", "input": docs}
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.embed_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        result = response.json()["embeddings"]
        logger.debug(f"response in {response.elapsed.total_seconds()} sec. for batch of size {np.array(result).shape}")
        return result