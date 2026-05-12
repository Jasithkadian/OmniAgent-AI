from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory, shared_memory
from agents.tools.code_executor import CodeAnalysisTool

CODING_PROMPT = """
You are the Lead Systems Engineer. Based on the research provided, design the technical architecture.
Objective: {objective}
Research: {research}

Specify the technology stack, module boundaries, and data flow.
"""

class CodingAgent(BaseAgent):
    name = "coding"

    def __init__(self, model=None):
        super().__init__(model, tools=[CodeAnalysisTool()])

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        research_findings = [f["content"] for f in state["findings"] if f["agent"] == "research"]
        
        # 1. Use Tool: Create implementation plan
        tool = CodeAnalysisTool()
        plan = tool.create_implementation_plan(objective, "\n".join(research_findings))
        
        # 2. 'Think' phase: Refine architecture
        analysis = await self.think(
            CODING_PROMPT.format(objective=objective, research=str(research_findings)),
            state
        )
        
        # 3. Create findings
        finding = AgentFinding(
            agent=self.name,
            title="Technical Architecture Design",
            content=f"Proposed stack: {', '.join(plan['recommended_stack'])}. Defined {len(plan['steps'])} implementation steps.",
            confidence=0.95,
            metadata={"stack": plan['recommended_stack']}
        )
        self.update_state(state, [finding])
        
        # 4. Save artifact
        state["artifacts"]["implementation_plan"] = plan
        
        # 5. Post to Blackboard
        await shared_blackboard.post_finding(
            workflow_id=str(state["workflow_id"]),
            agent=self.name,
            topic="architecture_design",
            content=plan,
            confidence=0.95
        )
        
        shared_memory.add_message(self.name, "Architecture design complete. Implementation plan stored in artifacts.")
        
        return state
