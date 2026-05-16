from typing import Any, List, Dict, Optional
from uuid import UUID
import logging
from pydantic import BaseModel, Field

from rag.retrieval.hybrid_search import HybridSearchService
from rag.store.chroma import ChromaVectorStore
from app.schemas.documents import DocumentSearchRequest

logger = logging.getLogger(__name__)

class DocumentSearchTool:
    """
    Agent tool for performing semantic search over ingested documents.
    """
    name = "document_search"
    description = "Searches for relevant information within the uploaded documents. Use this to gather context, facts, and citations."

    def __init__(self) -> None:
        self.search_service = HybridSearchService(ChromaVectorStore())

    async def ainvoke(self, user_id: UUID, query: str, document_ids: Optional[List[UUID]] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Executes the search.
        """
        logger.info(f"Tool {self.name} invoked with query: {query}")
        try:
            hits = await self.search_service.search(
                user_id=user_id,
                query=query,
                limit=limit,
                document_ids=document_ids
            )
            return [hit for hit in hits]
        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            return [{"error": str(e)}]

    def as_gemini_tool(self) -> Any:
        """
        Returns the tool definition in a format Gemini understands (Google's dynamic tool calling).
        """
        # For gemini-python SDK, we can just pass the function itself if it has type hints and docstrings
        return self.ainvoke
