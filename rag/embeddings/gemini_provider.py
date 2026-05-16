import asyncio
import logging
from typing import List
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from rag.embeddings.base import BaseEmbeddingProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Production-grade embedding provider using Google's Gemini models.
    Includes retry logic and batch processing.
    """
    def __init__(self, model_name: str = "models/text-embedding-004", task_type: str = "retrieval_document"):
        self.model_name = model_name
        self.task_type = task_type
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY not found in settings. Gemini embeddings will fail.")
        genai.configure(api_key=settings.gemini_api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def _embed_batch(self, texts: List[str], is_query: bool = False) -> List[List[float]]:
        # google-generativeai embed_content is synchronous, wrap in executor if needed for high throughput
        # or use its native batching.
        try:
            task = "retrieval_query" if is_query else self.task_type
            response = genai.embed_content(
                model=self.model_name,
                content=texts,
                task_type=task
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def embed_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """
        Embeds documents in batches to avoid API limits and excessive memory usage.
        """
        logger.info(f"Embedding {len(texts)} documents with {self.model_name}")
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self._embed_batch(batch)
            all_embeddings.extend(embeddings)
            
        return all_embeddings

    async def embed_query(self, text: str) -> List[float]:
        """Embeds a single query string."""
        logger.debug(f"Embedding query with {self.model_name}")
        embeddings = await self._embed_batch([text], is_query=True)
        return embeddings[0]
