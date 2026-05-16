from rag.embeddings.factory import embedding_factory

class EmbeddingProvider:
    """
    Legacy compatibility wrapper for the EmbeddingProvider.
    Delegates to the EmbeddingFactory.
    """
    def __init__(self, provider_type: str = "gemini"):
        self._provider = embedding_factory.get_provider(provider_type)

    async def embed_documents(self, texts):
        return await self._provider.embed_documents(texts)

    async def embed_query(self, text):
        return await self._provider.embed_query(text)
