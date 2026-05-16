import pytest
import os
from uuid import uuid4
from rag.ingestion.pipeline import rag_pipeline
from rag.retrieval.hybrid_search import HybridSearchService
from rag.store.chroma import ChromaVectorStore

@pytest.mark.asyncio
async def test_full_rag_flow_mock_file(tmp_path):
    # 1. Create a dummy text file
    d = tmp_path / "test_docs"
    d.mkdir()
    f = d / "test.txt"
    f.write_text("Veyra is a powerful orchestration platform. It uses LangGraph and RAG.")
    
    user_id = uuid4()
    doc_id = uuid4()
    
    # 2. Ingest
    # We need to mock the loaders if we want to run this without real PDF/DOCX dependencies in CI,
    # but since we installed them, we can try a TXT (fallback in pipeline).
    result = await rag_pipeline.ingest_document(str(f), user_id, doc_id)
    
    assert result["status"] == "success"
    assert result["chunks_created"] > 0
    
    # 3. Retrieve
    vector_store = ChromaVectorStore()
    search_service = HybridSearchService(vector_store)
    
    query = "What is Veyra?"
    hits = await search_service.search(user_id=user_id, query=query)
    
    assert len(hits) > 0
    assert "Veyra" in hits[0]["text"]
    assert hits[0]["score"] > 0.1
