import logging
from typing import Dict, List, Any
import asyncio

logger = logging.getLogger(__name__)

class SharedBlackboardMemory:
    """
    A concurrent, shared memory space (blackboard) for agents to post partial findings,
    resolve conflicts, and reach consensus during parallel execution.
    Backed by Redis pub/sub in production.
    """
    def __init__(self):
        self._blackboard: Dict[str, List[Dict[str, Any]]] = {}
        self._consensus: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def post_finding(self, workflow_id: str, agent: str, topic: str, content: Any, confidence: float):
        """Agents post their independent findings to the blackboard."""
        async with self._lock:
            if workflow_id not in self._blackboard:
                self._blackboard[workflow_id] = []
            
            entry = {
                "agent": agent,
                "topic": topic,
                "content": content,
                "confidence": confidence,
                "timestamp": __import__('time').time()
            }
            self._blackboard[workflow_id].append(entry)
            logger.debug(f"Blackboard received finding from {agent} on '{topic}'")

    async def resolve_conflicts(self, workflow_id: str, topic: str) -> Dict[str, Any]:
        """
        Supervisor evaluates conflicting findings on the blackboard and determines consensus.
        """
        async with self._lock:
            findings = [f for f in self._blackboard.get(workflow_id, []) if f["topic"] == topic]
            if not findings:
                return {}

            # Simple consensus: Highest confidence wins, or average numeric values.
            # In a real system, an LLM call would synthesize and resolve conflicts here.
            findings.sort(key=lambda x: x["confidence"], reverse=True)
            best_finding = findings[0]
            
            # Record consensus
            if workflow_id not in self._consensus:
                self._consensus[workflow_id] = {}
            
            consensus_result = {
                "topic": topic,
                "agreed_content": best_finding["content"],
                "contributors": list(set(f["agent"] for f in findings)),
                "consensus_score": best_finding["confidence"]
            }
            self._consensus[workflow_id][topic] = consensus_result
            logger.info(f"Consensus reached on '{topic}' with score {consensus_result['consensus_score']}")
            
            return consensus_result

    async def get_blackboard_state(self, workflow_id: str) -> Dict[str, Any]:
        return {
            "raw_findings": self._blackboard.get(workflow_id, []),
            "resolved_consensus": self._consensus.get(workflow_id, {})
        }

# Global singleton
shared_blackboard = SharedBlackboardMemory()
