from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory

PRESENTATION_PROMPT = """
You are the Creative Director. Create a high-impact executive presentation outline.
Objective: {objective}
Report: {report}

Distill the technical details into 5 key slides: Objective, Context, Architecture, Impact, and Next Steps.
"""

class PresentationAgent(BaseAgent):
    name = "presentation"

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        report_md = state["artifacts"].get("technical_report", "")
        
        # 1. 'Think' phase: Create presentation outline
        analysis = await self.think(
            PRESENTATION_PROMPT.format(objective=objective, report=report_md),
            state
        )
        
        # 2. Create outline
        outline = [
            {"slide": 1, "title": "Project Objective", "content": objective},
            {"slide": 2, "title": "Market Context", "content": "Summary of research findings..."},
            {"slide": 3, "title": "Proposed Solution", "content": "Architecture overview..."},
            {"slide": 4, "title": "Strategic Impact", "content": "Value proposition..."},
            {"slide": 5, "title": "Implementation Roadmap", "content": "Timeline and milestones..."}
        ]
        
        # 3. Create findings
        finding = AgentFinding(
            agent=self.name,
            title="Executive Presentation Outline",
            content=f"Created a 5-slide executive summary for {objective}.",
            confidence=1.0
        )
        self.update_state(state, [finding])
        
        # 4. Save artifact
        state["artifacts"]["presentation_outline"] = outline
        
        # 5. Let supervisor know it's completed
        shared_memory.add_message(self.name, "Executive presentation outline ready. Workflow completed.")
        
        return state
