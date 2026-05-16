import logging
from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState
from agents.core.memory import shared_memory
from agents.core.blackboard import shared_blackboard
from agents.task_delegation import task_delegator

logger = logging.getLogger(__name__)

SUPERVISOR_PROMPT = """
You are the Supervisor Agent. You orchestrate the workflow by evaluating task progress and deciding the next agent to execute.

Objective: {objective}
Tasks: {tasks}
Findings: {findings}

Assess if the current progress is sufficient to move to the next task or if the workflow is complete.
"""

class SupervisorAgent(BaseAgent):
    name = "supervisor"

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        workflow_id = str(state["workflow_id"])
        
        logger.info(f"Supervisor evaluating workflow: {workflow_id}")

        # 1. Resolve blackboard consensus (collaboration layer)
        await shared_blackboard.resolve_conflicts(workflow_id, "research_data")
        blackboard_state = await shared_blackboard.get_blackboard_state(workflow_id)
        
        # 2. Heuristic check: Find the next 'queued' task
        next_task = next((t for t in state["tasks"] if t["status"] == "queued"), None)
        
        if next_task:
            logger.info(f"Supervisor delegating next task to: {next_task['agent']}")
            state["next_step"] = next_task["agent"]
            shared_memory.add_message(self.name, f"Delegating next task to {next_task['agent']}: {next_task['title']}")
        else:
            # 3. LLM check: Assess if we are actually done or need more work
            # This handles edge cases where planning was incomplete
            analysis = await self.think(
                SUPERVISOR_PROMPT.format(
                    objective=objective, 
                    tasks=json.dumps(state["tasks"]), 
                    findings=json.dumps(state["findings"][:3]) # Limit context
                ),
                state
            )
            
            logger.info("All tasks completed. Finalizing workflow.")
            state["next_step"] = "__end__"
            state["status"] = "completed"
            shared_memory.add_message(self.name, "All planned tasks completed successfully. Workflow finalized.")
            
        return state

# Note: We need to import json inside the file or use json.dumps elsewhere.
import json
