import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

# Assume we reuse the RAG vector store for semantic memory
# In a highly specialized system, this might be a separate Chroma collection (e.g., "veyra_semantic_memory")
from rag.store.chroma import ChromaVectorStore
from rag.chunking.semantic_chunker import DocumentChunk

logger = logging.getLogger(__name__)

class SemanticMemory:
    """
    Vector-backed store for generalized knowledge, concepts, user preferences, and cross-workflow learnings.
    """
    def __init__(self):
        # Initialize a dedicated collection for semantic memory
        self.vector_store = ChromaVectorStore(collection_name="semantic_memory")

    async def add_knowledge(self, user_id: str, concept: str, category: str, content: str, importance: float = 1.0) -> None:
        """
        Indexes a generalized fact or learned behavior.
        """
        chunk = DocumentChunk(
            text=content,
            chunk_index=0,
            metadata={
                "user_id": user_id,
                "concept": concept,
                "category": category, # e.g., 'preference', 'technical_pattern', 'domain_fact'
                "importance": importance,
                "timestamp": __import__('time').time()
            }
        )
        await self.vector_store.add_chunks([chunk])
        logger.info(f"Indexed semantic knowledge for {user_id}: {concept}")

    async def search_knowledge(self, user_id: str, query: str, limit: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves relevant semantic memories using dense vector search.
        """
        filters = {"user_id": user_id}
        if category:
            filters["category"] = category
            
        results = await self.vector_store.search(query=query, limit=limit, filters=filters)
        logger.debug(f"Retrieved {len(results)} semantic memories for query: '{query}'")
        return results

# Singleton instance
semantic_memory_store = SemanticMemory()
