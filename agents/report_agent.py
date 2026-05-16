import logging
from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory

logger = logging.getLogger(__name__)

REPORT_PROMPT = """
You are the Technical Report Agent. Your task is to synthesize all research findings into a comprehensive, structured technical report.

Objective: {objective}
Findings: {findings}

Requirements:
1. Provide a clear executive summary.
2. Detail technical requirements and constraints.
3. Propose a high-level solution architecture.
4. Cite findings where appropriate.

Format the report in Markdown.
"""

class ReportAgent(BaseAgent):
    name = "report"

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        all_findings = [f["content"] for f in state["findings"]]
        
        logger.info(f"Report Agent synthesizing {len(all_findings)} findings.")

        # 1. Reasoning phase: Synthesize report
        report_content = await self.think(
            REPORT_PROMPT.format(objective=objective, findings="\n\n".join(all_findings)),
            state
        )
        
        # 2. Record final finding/artifact
        finding = AgentFinding(
            agent=self.name,
            title="Final Technical Synthesis Report",
            content=report_content,
            confidence=1.0
        )
        self.update_state(state, [finding])
        
        # 3. Mark task as completed
        current_task = next((t for t in state["tasks"] if t["agent"] == "report" and t["status"] == "queued"), None)
        if current_task:
            for t in state["tasks"]:
                if t["id"] == current_task["id"]:
                    t["status"] = "completed"
        
        # 4. Save to artifacts
        state["artifacts"]["final_report"] = report_content
        
        # 5. Route to Critic for verification
        state["next_step"] = "critic"
        
        shared_memory.add_message(self.name, "Final report generated and stored in artifacts.")
        
        return state
