import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from rag.store.chroma import ChromaVectorStore
from rag.store.bm25 import bm25_store
from app.core.config import settings

logger = logging.getLogger(__name__)

class RetrievalConfig:
    def __init__(self):
        self.top_k = getattr(settings, "retrieval_top_k", 5)
        self.similarity_threshold = getattr(settings, "similarity_threshold", 0.3)
        self.max_context_chunks = getattr(settings, "max_context_chunks", 10)

class HybridSearchService:
    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store
        self.config = RetrievalConfig()
        self._reranker = None

    @property
    def reranker(self):
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
        return self._reranker

    def _rrf(self, results_list: List[List[Dict]], k: int = 60) -> List[Dict]:
        fused_scores = {}
        content_map = {}
        for results in results_list:
            for rank, doc in enumerate(results):
                doc_id = doc["id"]
                fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + 1.0 / (rank + k)
                content_map[doc_id] = doc
        reranked_ids = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return [content_map[did] for did, _ in reranked_ids]

    async def search(
        self,
        user_id: UUID,
        query: str,
        limit: Optional[int] = None,
        document_ids: Optional[List[UUID]] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"Executing hybrid retrieval for user {user_id}")

        filters = {"user_id": str(user_id)}
        if document_ids:
            if len(document_ids) == 1:
                filters["document_id"] = str(document_ids[0])
            else:
                filters["document_id"] = {"$in": [str(doc_id) for doc_id in document_ids]}

        search_limit = limit or self.config.top_k
        fetch_k = search_limit * 4

        # 1. Parallel dense + sparse retrieval
        loop = asyncio.get_event_loop()
        dense_task = self.vector_store.search(query=query, limit=fetch_k, filters=filters)
        sparse_task = loop.run_in_executor(None, bm25_store.search, query, fetch_k)

        dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)

        # 2. Reciprocal Rank Fusion
        fused = self._rrf([dense_results, sparse_results])[:20]

        if not fused:
            return []

        # 3. Reranking
        pairs = [[query, doc.get("content", "")] for doc in fused]
        rerank_scores = await loop.run_in_executor(None, self.reranker.predict, pairs)

        for i, doc in enumerate(fused):
            doc["rerank_score"] = float(rerank_scores[i])

        results = sorted(fused, key=lambda x: x["rerank_score"], reverse=True)[:search_limit]
        logger.info(f"Hybrid retrieval returned {len(results)} results.")
        return results
