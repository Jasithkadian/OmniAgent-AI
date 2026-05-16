from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingProvider(ABC):
    """
    Interface for embedding providers to ensure modularity and swapability.
    """
    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of strings."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generate an embedding for a single query string."""
        pass
