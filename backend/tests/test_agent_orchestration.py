import pytest
import os
from uuid import uuid4
from agents.core.graph import veyra_graph

@pytest.mark.asyncio
async def test_agent_orchestration_flow():
    """
    Smoke test to verify the multi-agent orchestration lifecycle.
    Note: Requires GEMINI_API_KEY in environment to run fully.
    """
    user_id = uuid4()
    objective = "Analyze the impact of AI on software engineering."
    
    # Run the graph
    # In a real test, we might mock the LLM responses to avoid costs and variability
    # but for a production-grade infrastructure, we want to see it boot.
    try:
        final_state = await veyra_graph.run(
            user_id=user_id,
            objective=objective,
            document_ids=[]
        )
        
        assert final_state["status"] in ["completed", "failed"] # Even failure is a valid flow termination
        assert final_state["iteration_count"] > 0
        assert len(final_state["tasks"]) > 0
        
    except Exception as e:
        # If no API key, it will likely fail here
        pytest.fail(f"Agent orchestration crashed: {e}")

@pytest.mark.asyncio
async def test_agent_router_safety():
    from agents.core.router import router
    from agents.core.state import create_initial_state
    
    # Test Max Iterations
    state = create_initial_state(uuid4(), uuid4(), "Test objective")
    state["iteration_count"] = 21
    
    next_node = router(state)
    assert next_node == "__end__"
    assert "Max iteration limit reached." in state["errors"]
