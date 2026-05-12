from typing import List
from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory
from agents.core.blackboard import shared_blackboard
from agents.task_delegation import task_delegator

SUPERVISOR_PROMPT = """
You are the Supervisor Agent. You orchestrate the parallel execution of the agent swarm.
Objective: {objective}
Current Blackboard Consensus: {blackboard}

Evaluate the progress and decide the next steps.
"""

class SupervisorAgent(BaseAgent):
    name = "supervisor"

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        workflow_id = str(state["workflow_id"])
        
        # 1. Resolve conflicts on the blackboard from previous parallel runs
        await shared_blackboard.resolve_conflicts(workflow_id, "research_data")
        blackboard_state = await shared_blackboard.get_blackboard_state(workflow_id)
        
        # 2. Update state tasks based on blackboard consensus
        # (Mock logic: mark tasks as completed if we have consensus)
        if blackboard_state.get("resolved_consensus"):
            for task in state["tasks"]:
                if task["status"] == "running":
                    task["status"] = "completed"
        
        # 3. Use Delegation Engine to find next parallel branches
        next_branches = await task_delegator.evaluate_parallelism(objective, state["tasks"])
        
        # 4. 'Think' phase: Supervisor assesses the situation
        analysis = await self.think(
            SUPERVISOR_PROMPT.format(objective=objective, blackboard=str(blackboard_state["resolved_consensus"])),
            state
        )
        
        if next_branches:
            # Mark these tasks as running
            for task in state["tasks"]:
                if task["agent"] in next_branches and task["status"] == "queued":
                    task["status"] = "running"
                    
            state["next_step"] = next_branches
            state["parallel_branches"] = next_branches
            shared_memory.add_message(self.name, f"Delegating parallel tasks to: {', '.join(next_branches)}")
            
        else:
            # All tasks done, route to end
            state["next_step"] = "__end__"
            state["status"] = "completed"
            shared_memory.add_message(self.name, "All delegated tasks completed successfully.")
            
        return state
