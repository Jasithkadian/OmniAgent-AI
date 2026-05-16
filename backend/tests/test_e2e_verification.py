import pytest
import os
from uuid import uuid4
from rag.ingestion.pipeline import rag_pipeline
from agents.core.graph import veyra_graph

@pytest.mark.asyncio
async def test_e2e_workflow_with_verification(tmp_path):
    """
    Validates the complete lifecycle from document upload to verified technical report.
    """
    # 1. Setup Test Document
    test_dir = tmp_path / "e2e_test"
    test_dir.mkdir()
    test_file = test_dir / "architecture.txt"
    test_file.write_text(
        "Veyra uses a Supervisor-Worker agent pattern. "
        "The system relies on ChromaDB for persistent vector storage. "
        "Gemini 2.0 Flash is the primary LLM provider for reasoning."
    )
    
    user_id = uuid4()
    doc_id = uuid4()
    
    # 2. Ingestion Phase
    ingest_result = await rag_pipeline.ingest_document(str(test_file), user_id, doc_id)
    assert ingest_result["status"] == "success"
    
    # 3. Agent Orchestration Phase
    objective = "Explain the architecture of Veyra and its storage mechanism."
    
    final_state = await veyra_graph.run(
        user_id=user_id,
        objective=objective,
        document_ids=[doc_id]
    )
    
    # 4. Verification Assertions
    assert final_state["status"] == "completed"
    assert "final_report" in final_state["artifacts"]
    assert "verification_metrics" in final_state["artifacts"]
    
    v_metrics = final_state["artifacts"]["verification_metrics"]
    assert "hallucination_score" in v_metrics
    assert "citation_accuracy" in v_metrics
    assert v_metrics["is_verified"] is True
    
    # 5. Observability Check
    from app.api.v1.health import get_metrics
    metrics = await get_metrics()
    assert metrics["total_workflows"] >= 1
    assert "avg_duration_s" in metrics
    
    print(f"E2E Test Passed with Verification Score: {v_metrics.get('reasoning_quality')}")
