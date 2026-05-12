from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory
from agents.tools.document_search import DocumentSearchTool

from agents.core.blackboard import shared_blackboard

RESEARCH_PROMPT = """
You are the Lead Researcher. Your task is to extract meaningful insights from the following retrieved context.
Objective: {objective}
Context: {context}

Identify key themes, technical requirements, and potential blockers.
"""

class ResearchAgent(BaseAgent):
    name = "research"

    def __init__(self, model=None):
        super().__init__(model, tools=[DocumentSearchTool()])

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        workflow_id = str(state["workflow_id"])
        
        # 1. Use Tool: Search for relevant documents
        search_results = await self.use_tools(
            "document_search", 
            user_id=state["user_id"],
            query=objective,
            document_ids=state["document_ids"]
        )
        
        # 2. 'Think' phase: Process search results
        context_str = str(search_results)
        analysis = await self.think(
            RESEARCH_PROMPT.format(objective=objective, context=context_str),
            state
        )
        
        # 3. Create findings
        finding_content = f"Analyzed {len(search_results)} documents. Identified core requirements for {objective}."
        finding = AgentFinding(
            agent=self.name,
            title="Contextual Analysis",
            content=finding_content,
            confidence=0.9,
            metadata={"source_count": len(search_results)}
        )
        self.update_state(state, [finding])
        
        # 4. Post to Blackboard for collaboration
        await shared_blackboard.post_finding(
            workflow_id=workflow_id,
            agent=self.name,
            topic="research_data",
            content=finding_content,
            confidence=0.9
        )
        
        shared_memory.add_message(self.name, "Research phase completed. Findings posted to blackboard.")
        
        return state
