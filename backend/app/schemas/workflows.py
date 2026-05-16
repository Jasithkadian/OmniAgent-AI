from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    objective: str = Field(min_length=4, max_length=4000)
    conversation_id: Optional[UUID] = None
    document_ids: list[UUID] = Field(default_factory=list)


class WorkflowRunResponse(BaseModel):
    workflow_id: UUID
    status: str
    findings: list[dict]
    messages: list[dict]
    artifacts: dict
