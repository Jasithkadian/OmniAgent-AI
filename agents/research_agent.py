import logging
import json
from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory
from agents.tools.document_search import DocumentSearchTool
from agents.core.blackboard import shared_blackboard

logger = logging.getLogger(__name__)

RESEARCH_PROMPT = """
You are the Lead Researcher. Your task is to perform semantic search and extract meaningful insights to solve the user's objective.

Objective: {objective}
Task: {task_objective}

Use the 'document_search' tool to gather context from the uploaded documents. 
Analyze the results and identify key technical requirements, facts, and constraints.
"""

class ResearchAgent(BaseAgent):
    name = "research"

    def __init__(self, model_name: str = "models/gemini-2.0-flash"):
        super().__init__(model_name=model_name, tools=[DocumentSearchTool()])

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        workflow_id = str(state["workflow_id"])
        
        # 1. Identify current task objective
        current_task = next((t for t in state["tasks"] if t["agent"] == "research" and t["status"] == "queued"), None)
        task_objective = current_task["objective"] if current_task else objective

        # 2. LLM Reasoning with Tool Access
        # We wrap the prompt and provide context about the current state
        full_prompt = RESEARCH_PROMPT.format(objective=objective, task_objective=task_objective)
        
        # We need to pass user_id and document_ids to the tool when called.
        # Gemini's automatic function calling handles the arguments, but we need to ensure 
        # the agent 'knows' these IDs. We can inject them into the prompt or rely on them 
        # being available in the tool context if we refactored it. 
        # For now, we'll inject into prompt.
        
        full_prompt += f"\n\nContext:\nUser ID: {state['user_id']}\nDocument IDs: {state['document_ids']}"

        analysis = await self.think(full_prompt, state)
        
        # 3. Create findings
        finding = AgentFinding(
            agent=self.name,
            title="Contextual Research Analysis",
            content=analysis,
            confidence=0.9,
            metadata={"task": task_objective}
        )
        self.update_state(state, [finding])
        
        # 4. Mark task as completed
        if current_task:
            for t in state["tasks"]:
                if t["id"] == current_task["id"]:
                    t["status"] = "completed"
        
        # 5. Post to Blackboard for collaboration
        await shared_blackboard.post_finding(
            workflow_id=workflow_id,
            agent=self.name,
            topic="research_data",
            content=analysis,
            confidence=0.9
        )
        
        # 6. Route to Supervisor for next task evaluation
        state["next_step"] = "supervisor"
        
        shared_memory.add_message(self.name, "Research completed and findings synthesized.")
        
        return state
