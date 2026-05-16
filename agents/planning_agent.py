import uuid
import json
import logging
from typing import List
from pydantic import BaseModel, Field
from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding, AgentTask
from agents.core.memory import shared_memory

logger = logging.getLogger(__name__)

class PlanResponse(BaseModel):
    """Schema for the planning agent's response."""
    rationale: str = Field(description="The reasoning behind the proposed plan")
    tasks: List[AgentTask] = Field(description="A list of discrete tasks for specialized agents")

PLANNING_PROMPT = """
You are the Lead Veyra Architect. Your job is to analyze the user's objective and break it down into a sequence of tasks for specialized agents.

Objective: {objective}

Available Agents:
- research: Deep context retrieval and information gathering using the document search tool.
- coding: Implementation design, technical architecture, and prototyping.
- report: Technical synthesis, structured documentation, and final report generation.

Guidelines:
1. Break the objective into 3-5 discrete, actionable tasks.
2. Every plan MUST start with 'research' if document context is required.
3. Every plan MUST end with 'report' to synthesize the final output.
4. Ensure tasks are logically ordered with clear dependencies.
5. Be extremely specific about the 'objective' for each task. Avoid generic descriptions.

Return your response in structured JSON format following this schema:
{{
  "rationale": "Detailed explanation of the architectural approach and task sequencing",
  "tasks": [
    {{
      "id": "task_1",
      "agent": "research",
      "title": "Initial Fact Gathering",
      "objective": "Retrieve specific technical details regarding...",
      "depends_on": []
    }}
  ]
}}
"""

class PlanningAgent(BaseAgent):
    name = "planning"

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        
        # 1. 'Think' phase using real LLM
        prompt = PLANNING_PROMPT.format(objective=objective)
        
        # We use a specialized system prompt for planning
        logger.info(f"Planning Agent generating roadmap for: {objective}")
        
        # Call Gemini to get the plan
        # We'll use a chat session to ensure JSON output
        chat = self.model.start_chat()
        response = await chat.send_message_async(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        try:
            plan_data = json.loads(response.text)
            
            # 2. Update state with tasks
            tasks = plan_data.get("tasks", [])
            for task in tasks:
                # Ensure each task has a unique ID if not provided
                if not task.get("id"):
                    task["id"] = str(uuid.uuid4())
                state["tasks"].append(task)
            
            # 3. Record finding
            finding = AgentFinding(
                agent=self.name,
                title="Strategic Roadmap Finalized",
                content=f"Plan rationale: {plan_data.get('rationale', 'N/A')}. Tasks created: {len(tasks)}.",
                confidence=1.0,
                metadata={"rationale": plan_data.get("rationale")}
            )
            self.update_state(state, [finding])
            
            # 4. Set next step
            if tasks:
                state["next_step"] = tasks[0]["agent"]
            else:
                state["next_step"] = "__end__"
                
            state["status"] = "running"
            shared_memory.add_message(self.name, f"Plan created: {plan_data.get('rationale')}")
            
        except Exception as e:
            logger.error(f"Failed to parse planning response: {e}")
            state["errors"].append(f"Planning failure: {str(e)}")
            state["status"] = "failed"
            
        return state
