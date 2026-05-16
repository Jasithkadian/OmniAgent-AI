import time
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from dataclasses import dataclass

from rag.retrieval.hybrid_search import HybridSearchService
from rag.store.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)

@dataclass
class RetrievalMetrics:
    precision_at_k: float
    recall_at_k: float
    mrr: float # Mean Reciprocal Rank
    latency_ms: float
    total_hits: int

class RetrievalEvaluator:
    """
    Framework for evaluating RAG retrieval quality.
    Measures precision, recall, and latency against benchmark datasets.
    """
    def __init__(self, search_service: Optional[HybridSearchService] = None):
        self.search_service = search_service or HybridSearchService(ChromaVectorStore())

    async def evaluate_query(
        self, 
        user_id: UUID, 
        query: str, 
        expected_chunk_ids: List[str], 
        k: int = 5
    ) -> RetrievalMetrics:
        """
        Evaluates a single query against a set of ground truth chunk IDs.
        """
        start_time = time.time()
        
        # 1. Execute retrieval
        hits = await self.search_service.search(user_id=user_id, query=query, limit=k)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # 2. Calculate metrics
        retrieved_ids = [hit.get("id") for hit in hits]
        
        # Intersection
        relevant_retrieved = [rid for retrieved_id in retrieved_ids if retrieved_id in expected_chunk_ids]
        
        precision = len(relevant_retrieved) / len(retrieved_ids) if retrieved_ids else 0.0
        recall = len(relevant_retrieved) / len(expected_chunk_ids) if expected_chunk_ids else 1.0
        
        # MRR calculation
        mrr = 0.0
        for i, retrieved_id in enumerate(retrieved_ids):
            if retrieved_id in expected_chunk_ids:
                mrr = 1.0 / (i + 1)
                break
                
        metrics = RetrievalMetrics(
            precision_at_k=precision,
            recall_at_k=recall,
            mrr=mrr,
            latency_ms=latency_ms,
            total_hits=len(hits)
        )
        
        logger.info(f"Retrieval Evaluation for '{query[:30]}...': Precision@{k}={precision:.2f}, Recall@{k}={recall:.2f}, MRR={mrr:.2f}")
        return metrics

    async def benchmark_dataset(self, user_id: UUID, benchmark_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs evaluation over a full dataset.
        Format: [{"query": "...", "expected_ids": ["..."]}, ...]
        """
        all_metrics = []
        for item in benchmark_data:
            m = await self.evaluate_query(user_id, item["query"], item["expected_ids"])
            all_metrics.append(m)
            
        # Aggregate
        avg_precision = sum(m.precision_at_k for m in all_metrics) / len(all_metrics)
        avg_recall = sum(m.recall_at_k for m in all_metrics) / len(all_metrics)
        avg_mrr = sum(m.mrr for m in all_metrics) / len(all_metrics)
        avg_latency = sum(m.latency_ms for m in all_metrics) / len(all_metrics)
        
        summary = {
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "avg_mrr": avg_mrr,
            "avg_latency_ms": avg_latency,
            "total_queries": len(benchmark_data)
        }
        
        logger.info(f"Benchmark Results: {summary}")
        return summary
