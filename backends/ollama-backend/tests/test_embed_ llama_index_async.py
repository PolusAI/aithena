"""Simple example of using the OllamaEmbedding class to get embeddings asynchronously."""

import asyncio
from llama_index.embeddings.ollama import OllamaEmbedding

async def main():
    ollama_embedding = OllamaEmbedding(
        model_name="nomic-embed-text",
        base_url="http://localhost:11434",
        ollama_additional_kwargs={"mirostat": 0},
    )

    pass_embedding = await ollama_embedding.aget_text_embedding_batch(
        ["This is a passage!", "This is another passage"], show_progress=True
    )
    print(pass_embedding)

    query_embedding = await ollama_embedding.aget_query_embedding("Where is blue?")
    print(query_embedding)

if __name__ == "__main__":
    asyncio.run(main())