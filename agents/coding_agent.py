from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory
from agents.core.blackboard import shared_blackboard

CODING_PROMPT = """
You are the Lead Systems Engineer. Based on the research provided, design the technical architecture.
Objective: {objective}
Research: {research}

Specify the technology stack, module boundaries, and data flow.
"""

class CodingAgent(BaseAgent):
    name = "coding"

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        research_findings = [f["content"] for f in state["findings"] if f["agent"] == "research"]
        
        # 1. Reasoning phase: Design architecture
        # We don't have the CodeAnalysisTool anymore, we'll rely on LLM reasoning
        analysis = await self.think(
            CODING_PROMPT.format(objective=objective, research="\n".join(research_findings)),
            state
        )
        
        # 2. Create findings
        finding = AgentFinding(
            agent=self.name,
            title="Technical Architecture Design",
            content=analysis,
            confidence=0.9
        )
        self.update_state(state, [finding])
        
        # 3. Save artifact
        state["artifacts"]["architecture_design"] = analysis
        
        # 4. Post to Blackboard
        await shared_blackboard.post_finding(
            workflow_id=str(state["workflow_id"]),
            agent=self.name,
            topic="architecture_design",
            content=analysis,
            confidence=0.9
        )
        
        shared_memory.add_message(self.name, "Architecture design complete. Findings posted to blackboard.")
        
        return state
