from typing import Any, List, Union
import logging
from agents.core.state import WorkflowState, AgentName

logger = logging.getLogger(__name__)

def router(state: WorkflowState) -> Union[List[str], str]:
    """
    Conditional router that determines the next agent(s) to execute.
    Enhanced with safety limits and dynamic branching.
    """
    # 1. Safety Limit: Max Iterations
    # Prevents infinite loops in autonomous reasoning
    if state.get("iteration_count", 0) > 20:
        logger.error("Workflow reached max iteration limit (20). Forcing termination.")
        state["errors"].append("Max iteration limit reached.")
        state["status"] = "failed"
        return "__end__"

    # 2. Check for explicit failure
    if state.get("status") == "failed":
        logger.error(f"Workflow failed: {state.get('errors')}")
        return "__end__"

    # 3. Get the next step from state
    next_step = state.get("next_step")
    
    if not next_step or next_step == "__end__":
        return "__end__"
        
    # 4. Handle parallel branching
    if isinstance(next_step, list):
        logger.info(f"Routing to parallel branches: {next_step}")
        return next_step
        
    # 5. Handle single agent routing
    # Validate that the agent name is valid
    valid_agents = ["planning", "supervisor", "research", "coding", "report", "presentation", "browser", "critic"]
    if next_step in valid_agents:
        logger.info(f"Routing to next agent: {next_step}")
        return next_step

    logger.warning(f"Invalid next_step '{next_step}'. Terminating workflow.")
    return "__end__"
