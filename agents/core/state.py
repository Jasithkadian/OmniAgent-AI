from typing import Annotated, Any, Literal, TypedDict, Optional, Union
import operator
from uuid import UUID
from pydantic import BaseModel, Field

AgentName = Literal["planning", "supervisor", "research", "coding", "report", "presentation", "browser"]
WorkflowStatus = Literal["queued", "running", "completed", "failed"]

class AgentFinding(BaseModel):
    agent: AgentName
    title: str
    content: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    citations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class AgentTask(BaseModel):
    id: str
    agent: AgentName
    title: str
    objective: str
    depends_on: list[str] = Field(default_factory=list)
    status: WorkflowStatus = "queued"
    consensus_score: float = 0.0

class AgentMessage(BaseModel):
    agent: AgentName
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class WorkflowState(TypedDict):
    # Workflow Metadata
    workflow_id: UUID
    user_id: UUID
    conversation_id: Optional[UUID]
    objective: str
    status: WorkflowStatus
    
    # State Reducers (Annotated with operator.add allows merging instead of overwriting)
    # This is critical for parallel LangGraph execution where multiple nodes return state
    tasks: Annotated[list[dict[str, Any]], operator.add]
    findings: Annotated[list[dict[str, Any]], operator.add]
    messages: Annotated[list[dict[str, Any]], operator.add]
    errors: Annotated[list[str], operator.add]
    
    # Parallel Routing State
    parallel_branches: list[AgentName]
    
    # Conventional State
    active_agent: Optional[AgentName]
    artifacts: dict[str, Any]
    document_ids: list[UUID]
    
    # Routing and Control
    next_step: Optional[Union[str, list[str]]]
    iteration_count: int

def create_initial_state(
    workflow_id: UUID,
    user_id: UUID,
    objective: str,
    conversation_id: Optional[UUID] = None,
    document_ids: Optional[list[UUID]] = None,
) -> WorkflowState:
    return {
        "workflow_id": workflow_id,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "objective": objective,
        "status": "queued",
        "tasks": [],
        "findings": [],
        "messages": [],
        "errors": [],
        "parallel_branches": [],
        "active_agent": None,
        "artifacts": {},
        "document_ids": document_ids or [],
        "next_step": None,
        "iteration_count": 0,
    }
