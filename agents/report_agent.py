from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory
from agents.tools.report_writer import ReportWriterTool

REPORT_PROMPT = """
You are the Technical Writer. Synthesize the findings from Research and Coding into a professional report.
Objective: {objective}
Findings: {findings}

Ensure the report is structured, clear, and actionable.
"""

class ReportAgent(BaseAgent):
    name = "report"

    def __init__(self, model=None):
        super().__init__(model, tools=[ReportWriterTool()])

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        all_findings = [AgentFinding(**f) for f in state["findings"]]
        
        # 1. Use Tool: Compose markdown
        tool = ReportWriterTool()
        report_md = tool.compose_markdown(objective, all_findings)
        
        # 2. 'Think' phase: Review and polish
        analysis = await self.think(
            REPORT_PROMPT.format(objective=objective, findings=str(state["findings"])),
            state
        )
        
        # 3. Create findings
        finding = AgentFinding(
            agent=self.name,
            title="Technical Synthesis Report",
            content=f"Generated {len(report_md.splitlines())} lines of technical documentation.",
            confidence=1.0
        )
        self.update_state(state, [finding])
        
        # 4. Save artifact
        state["artifacts"]["technical_report"] = report_md
        
        shared_memory.add_message(self.name, "Technical report synthesized and available in artifacts.")
        
        return state
