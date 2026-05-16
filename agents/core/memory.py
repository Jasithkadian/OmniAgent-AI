from typing import Any, Optional
from uuid import UUID
from agents.core.state import AgentFinding, AgentMessage, AgentName, WorkflowState

class SharedMemory:
    """
    Handles shared memory across agents.
    In a real production app, this would interface with Redis or a Vector DB.
    """
    def __init__(self):
        self.context_window: list[AgentMessage] = []
        self.knowledge_base: list[AgentFinding] = []
        self.artifacts: dict[str, Any] = {}

    def add_message(self, agent: AgentName, content: str, metadata: Optional[dict[str, Any]] = None):
        msg = AgentMessage(agent=agent, content=content, metadata=metadata or {})
        self.context_window.append(msg)

    def add_finding(self, finding: AgentFinding):
        self.knowledge_base.append(finding)

    def set_artifact(self, key: str, value: Any):
        self.artifacts[key] = value

    def get_context(self) -> str:
        """Returns a string representation of the shared context."""
        context = "--- SHARED CONTEXT ---\n"
        for msg in self.context_window[-10:]: # Last 10 messages
            context += f"[{msg.agent}]: {msg.content}\n"
        
        context += "\n--- KEY FINDINGS ---\n"
        for finding in self.knowledge_base:
            context += f"- {finding.title}: {finding.content}\n"
        
        return context

# Singleton for demonstration, though in production we'd use dependency injection
# and per-workflow instances.
shared_memory = SharedMemory()
