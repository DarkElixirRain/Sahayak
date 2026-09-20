import logging
from typing import List, Union

import httpx

from core.config import get_settings
from core.embedding.base_embedding_model import BaseEmbeddingModel
from core.models.chunk import Chunk

logger = logging.getLogger(__name__)


class OllamaEmbeddingModel(BaseEmbeddingModel):
    """
    Direct Ollama embedding model implementation.
    Bypasses LiteLLM to avoid compatibility issues.
    """

    def __init__(self, model_name: str = "nomic-embed-text", api_base: str = "http://localhost:11434"):
        """
        Initialize Ollama embedding model.

        Args:
            model_name: The Ollama model name (e.g., "nomic-embed-text")
            api_base: The Ollama API base URL
        """
        self.model_name = model_name
        self.api_base = api_base.rstrip("/")
        settings = get_settings()
        self.dimensions = settings.VECTOR_DIMENSIONS
        
        logger.info(f"Initialized Ollama embedding model with model={model_name}, api_base={api_base}")

    async def embed_for_ingestion(self, chunks: Union[Chunk, List[Chunk]]) -> List[List[float]]:
        """
        Generate embeddings for chunks during ingestion.

        Args:
            chunks: Single chunk or list of chunks to embed

        Returns:
            List of embedding vectors
        """
        # Convert single chunk to list
        if isinstance(chunks, Chunk):
            chunks = [chunks]
        
        # Extract content from chunks (Chunk uses 'content', not 'text')
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings
        return await self.embed_documents(texts)

    async def embed_for_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        return await self.embed_query(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents using Ollama API.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        # Maximum characters - very conservative for non-Latin scripts like Nepali
        # Nepali Devanagari uses more tokens per character than English
        # nomic-embed-text has 8192 token limit, Nepali can be ~1-2 tokens per char
        MAX_CHARS = 4000  # Very conservative limit for Nepali text
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                try:
                    # Always truncate to be safe
                    original_len = len(text)
                    truncated_text = text[:MAX_CHARS]
                    
                    if original_len > MAX_CHARS:
                        logger.warning(f"Truncating text from {original_len} to {MAX_CHARS} characters for embedding")
                    
                    response = await client.post(
                        f"{self.api_base}/api/embed",
                        json={"model": self.model_name, "input": truncated_text},
                    )
                    
                    if response.status_code != 200:
                        error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                        logger.error(error_msg)
                        # Log the text length for debugging
                        logger.error(f"Failed text length: {len(truncated_text)} chars")
                        raise Exception(error_msg)
                    
                    result = response.json()
                    embedding = result["embeddings"][0]
                    embeddings.append(embedding)
                    
                except Exception as e:
                    logger.error(f"Error generating embedding for text (length={len(text)}): {e}")
                    raise
        
        return embeddings

    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        embeddings = await self.embed_documents([text])
        return embeddings[0]
