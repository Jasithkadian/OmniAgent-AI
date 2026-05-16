from uuid import UUID

from agents.core.graph import veyra_graph
from app.schemas.workflows import WorkflowRunRequest, WorkflowRunResponse


class WorkflowService:
    async def run(self, user_id: UUID, request: WorkflowRunRequest) -> WorkflowRunResponse:
        state = await veyra_graph.run(
            user_id=user_id,
            objective=request.objective,
            conversation_id=request.conversation_id,
            document_ids=request.document_ids,
        )
        return WorkflowRunResponse(
            workflow_id=state["workflow_id"],
            status=state["status"],
            findings=state["findings"],
            messages=state["messages"],
            artifacts=state["artifacts"],
        )

