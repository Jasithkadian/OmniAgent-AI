import logging
from typing import List, Dict, Any
from agents.core.state import AgentTask, AgentName

logger = logging.getLogger(__name__)

class TaskDelegationEngine:
    """
    Analyzes complex objectives and breaks them down into independent
    tasks that can be executed concurrently by specialized agents.
    """
    @staticmethod
    async def evaluate_parallelism(objective: str, tasks: List[Dict[str, Any]]) -> List[AgentName]:
        """
        Determines which agents can run in parallel based on the current state and remaining tasks.
        """
        logger.info("Evaluating task delegation and parallel branches...")
        
        # Simple heuristic: If research and browser tasks exist and are queued, run them concurrently.
        queued_agents = [task["agent"] for task in tasks if task["status"] == "queued"]
        
        parallel_candidates = []
        if "research" in queued_agents:
            parallel_candidates.append("research")
        if "browser" in queued_agents:
            parallel_candidates.append("browser")
            
        # If we have coding, it usually depends on research. We run it alone or in parallel 
        # with browser if they are independent.
        if "coding" in queued_agents and not parallel_candidates:
            parallel_candidates.append("coding")
            
        if "report" in queued_agents and not parallel_candidates:
            parallel_candidates.append("report")
            
        if "presentation" in queued_agents and not parallel_candidates:
            parallel_candidates.append("presentation")

        return parallel_candidates

task_delegator = TaskDelegationEngine()
