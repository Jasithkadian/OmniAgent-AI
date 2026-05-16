import time
import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class WorkflowMetrics:
    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: float = 0.0
    token_usage: int = 0
    iteration_count: int = 0
    status: str = "running"
    agent_timings: Dict[str, float] = field(default_factory=dict)
    hallucination_detected: bool = False
    verification_score: float = 0.0

class ObservabilityManager:
    """
    Central manager for platform observability and metrics.
    Tracks workflow performance, latency, and reliability.
    """
    def __init__(self):
        self.active_metrics: Dict[str, WorkflowMetrics] = {}
        self.completed_metrics: List[WorkflowMetrics] = []

    def start_workflow(self, workflow_id: str):
        self.active_metrics[workflow_id] = WorkflowMetrics(
            workflow_id=workflow_id,
            start_time=time.time()
        )
        logger.info(f"Observability: Started tracking workflow {workflow_id}")

    def end_workflow(self, workflow_id: str, status: str = "completed"):
        if workflow_id in self.active_metrics:
            m = self.active_metrics[workflow_id]
            m.end_time = time.time()
            m.duration = m.end_time - m.start_time
            m.status = status
            self.completed_metrics.append(m)
            del self.active_metrics[workflow_id]
            logger.info(f"Observability: Workflow {workflow_id} finished in {m.duration:.2f}s with status {status}")

    def record_agent_time(self, workflow_id: str, agent_name: str, duration: float):
        if workflow_id in self.active_metrics:
            self.active_metrics[workflow_id].agent_timings[agent_name] = duration

    def record_token_usage(self, workflow_id: str, tokens: int):
        if workflow_id in self.active_metrics:
            self.active_metrics[workflow_id].token_usage += tokens

    def record_verification(self, workflow_id: str, score: float, hallucination: bool):
        if workflow_id in self.active_metrics:
            self.active_metrics[workflow_id].verification_score = score
            self.active_metrics[workflow_id].hallucination_detected = hallucination

    def get_summary_metrics(self) -> Dict[str, Any]:
        if not self.completed_metrics:
            return {"status": "no data"}
            
        total_duration = sum(m.duration for m in self.completed_metrics)
        avg_duration = total_duration / len(self.completed_metrics)
        hallucination_rate = sum(1 for m in self.completed_metrics if m.hallucination_detected) / len(self.completed_metrics)
        
        return {
            "total_workflows": len(self.completed_metrics),
            "avg_duration_s": avg_duration,
            "hallucination_rate": hallucination_rate,
            "success_rate": sum(1 for m in self.completed_metrics if m.status == "completed") / len(self.completed_metrics),
            "avg_token_usage": sum(m.token_usage for m in self.completed_metrics) / len(self.completed_metrics)
        }

# Global instance
obs_manager = ObservabilityManager()
