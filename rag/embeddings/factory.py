from typing import Optional
from rag.embeddings.base import BaseEmbeddingProvider
from rag.embeddings.gemini_provider import GeminiEmbeddingProvider

class EmbeddingFactory:
    """
    Factory to manage and provide different embedding providers.
    """
    @staticmethod
    def get_provider(provider_type: str = "gemini") -> BaseEmbeddingProvider:
        if provider_type.lower() == "gemini":
            return GeminiEmbeddingProvider()
        # Future providers can be added here (e.g., openai, voyage)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider_type}")

embedding_factory = EmbeddingFactory()
