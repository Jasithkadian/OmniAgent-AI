from typing import Any, AsyncGenerator, Literal, List, Union
from uuid import UUID, uuid4
import logging

from langgraph.graph import END, StateGraph

from agents.core.state import WorkflowState, create_initial_state
from agents.planning_agent import PlanningAgent
from agents.supervisor_agent import SupervisorAgent
from agents.research_agent import ResearchAgent
from agents.coding_agent import CodingAgent
from agents.report_agent import ReportAgent
from agents.presentation_agent import PresentationAgent
from agents.browser_agent import BrowserAgent

logger = logging.getLogger(__name__)

def router(state: WorkflowState) -> Union[List[str], str]:
    """
    Conditional router that determines the next agent(s) to execute.
    Supports fan-out (returning a list of nodes for parallel execution).
    """
    next_step = state.get("next_step")
    
    if state.get("status") == "failed":
        logger.error(f"Workflow failed: {state.get('errors')}")
        return "__end__"
        
    if not next_step:
        return "__end__"
        
    # If it's a list, we return it to execute branches in parallel
    if isinstance(next_step, list):
        return next_step
        
    if next_step == "__end__":
        return "__end__"
    
    return next_step

class OmniAgentGraph:
    def __init__(self):
        self.builder = StateGraph(WorkflowState)
        self._register_nodes()
        self._register_edges()
        self.graph = self.builder.compile()

    def _register_nodes(self):
        self.builder.add_node("planning", PlanningAgent())
        self.builder.add_node("supervisor", SupervisorAgent())
        self.builder.add_node("research", ResearchAgent())
        self.builder.add_node("browser", BrowserAgent())
        self.builder.add_node("coding", CodingAgent())
        self.builder.add_node("report", ReportAgent())
        self.builder.add_node("presentation", PresentationAgent())

    def _register_edges(self):
        # 1. Entry point goes to planning
        self.builder.set_entry_point("planning")
        
        # 2. Planning delegates initial control to Supervisor
        self.builder.add_edge("planning", "supervisor")
        
        # 3. Supervisor -> Router (Fan-out to parallel agents or END)
        self.builder.add_conditional_edges(
            "supervisor",
            router,
            ["research", "browser", "coding", "report", "presentation", "__end__"]
        )
        
        # 4. Parallel workers fan-in back to Supervisor for evaluation
        self.builder.add_edge("research", "supervisor")
        self.builder.add_edge("browser", "supervisor")
        self.builder.add_edge("coding", "supervisor")
        self.builder.add_edge("report", "supervisor")
        self.builder.add_edge("presentation", "supervisor")

    async def run(
        self,
        user_id: UUID,
        objective: str,
        conversation_id: UUID | None = None,
        workflow_id: UUID | None = None,
        document_ids: List[UUID] | None = None,
        stream: bool = False
    ) -> WorkflowState | AsyncGenerator[dict, Any]:
        """
        Executes the workflow with optional streaming.
        """
        initial_state = create_initial_state(
            workflow_id=workflow_id or uuid4(),
            user_id=user_id,
            objective=objective,
            conversation_id=conversation_id,
            document_ids=document_ids
        )
        
        if stream:
            return self.graph.astream(initial_state)
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state

# Main instance
omniagent_graph = OmniAgentGraph()
