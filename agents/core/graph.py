from typing import Any, AsyncGenerator, Literal, List, Union, Optional
from uuid import UUID, uuid4
import logging

from langgraph.graph import END, StateGraph

from agents.core.state import WorkflowState, create_initial_state
from app.core.observability import obs_manager
from agents.planning_agent import PlanningAgent
from agents.supervisor_agent import SupervisorAgent
from agents.research_agent import ResearchAgent
from agents.coding_agent import CodingAgent
from agents.report_agent import ReportAgent
from agents.critic_agent import CriticAgent
# from agents.presentation_agent import PresentationAgent
# from agents.browser_agent import BrowserAgent

logger = logging.getLogger(__name__)

from agents.core.router import router

class VeyraGraph:
    def __init__(self):
        self.builder = StateGraph(WorkflowState)
        self._register_nodes()
        self._register_edges()
        self.graph = self.builder.compile()

    def _register_nodes(self):
        self.builder.add_node("planning", PlanningAgent())
        self.builder.add_node("supervisor", SupervisorAgent())
        self.builder.add_node("research", ResearchAgent())
        self.builder.add_node("coding", CodingAgent())
        self.builder.add_node("report", ReportAgent())
        self.builder.add_node("critic", CriticAgent())

    def _register_edges(self):
        # 1. Entry point goes to planning
        self.builder.set_entry_point("planning")
        
        # 2. Sequential nodes
        self.builder.add_edge("planning", "supervisor")
        
        # 3. Dynamic routing from Supervisor
        # The router will determine which worker to run next or to END
        self.builder.add_conditional_edges(
            "supervisor",
            router,
            ["research", "coding", "report", "critic", "__end__"]
        )
        
        # 4. Workers always return to Supervisor for evaluation
        self.builder.add_edge("research", "supervisor")
        self.builder.add_edge("coding", "supervisor")
        self.builder.add_edge("report", "critic")
        self.builder.add_edge("critic", "supervisor")

    async def run(
        self,
        user_id: UUID,
        objective: str,
        conversation_id: Optional[UUID] = None,
        workflow_id: Optional[UUID] = None,
        document_ids: Optional[List[UUID]] = None,
        stream: bool = False
    ) -> Union[WorkflowState, AsyncGenerator[dict, Any]]:
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
        
        # Start tracking
        wf_id = initial_state["workflow_id"]
        obs_manager.start_workflow(str(wf_id))
        
        try:
            final_state = await self.graph.ainvoke(initial_state)
            obs_manager.end_workflow(str(wf_id), status=final_state.get("status", "completed"))
            return final_state
        except Exception as e:
            obs_manager.end_workflow(str(wf_id), status="failed")
            raise

# Main instance
veyra_graph = VeyraGraph()
