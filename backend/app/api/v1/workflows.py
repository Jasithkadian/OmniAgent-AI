import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from agents.core.graph import veyra_graph
from agents.core.state import create_initial_state
from agents.core.memory import shared_memory
from uuid import uuid4
from app.core.config import settings

from app.api.deps import get_current_user
from app.core.security import UserPrincipal
from app.schemas.workflows import WorkflowRunRequest, WorkflowRunResponse
from app.services.workflows import WorkflowService

router = APIRouter()


@router.post("/run", response_model=WorkflowRunResponse)
async def run_workflow(
    request: WorkflowRunRequest,
    current_user: UserPrincipal = Depends(get_current_user),
) -> WorkflowRunResponse:
    return await WorkflowService().run(user_id=current_user.user_id, request=request)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    workflow_id: Optional[UUID] = None,
    last_message_id: Optional[str] = None
):
    """
    WebSocket endpoint with recovery and persistence.
    Usage: /ws?token=XYZ&workflow_id=UUID&last_message_id=123-0
    """
    await websocket.accept()
    
    # 1. Auth check
    if not token:
        await websocket.close(code=4001)
        return
    try:
        from app.core.security import clerk_auth
        user_principal = await clerk_auth.verify_token(token)
        user_id = UUID(user_principal.user_id)
    except Exception:
        await websocket.close(code=4001)
        return

    try:
        # 2. Recovery logic
        if workflow_id and last_message_id:
            from app.core.redis import redis_event_store
            missed_events = await redis_event_store.get_events_since(str(workflow_id), last_message_id)
            for event in missed_events:
                await websocket.send_json(event)

        # 3. New Workflow Execution or Attachment
        # If workflow_id is provided but it's already running, we might just want to listen.
        # For this task, we assume the initial message starts a new one or we attach.
        data = await websocket.receive_text()
        payload = json.loads(data)
        
        objective = payload.get("objective")
        document_ids = payload.get("document_ids", [])
        
        # In a real system, we'd check if this workflow_id is already active in a worker.
        current_workflow_id = workflow_id or uuid4()

        state = create_initial_state(
            workflow_id=current_workflow_id,
            user_id=user_id,
            conversation_id=None,
            objective=objective,
            document_ids=document_ids,
        )
        
        from app.core.redis import redis_event_store
        
        async for event in veyra_graph.graph.astream_events(state, version="v2"):
            # Prepare event payload
            out_event = {
                "event": event["event"],
                "name": event["name"],
                "data": event.get("data", {}),
                "workflow_id": str(current_workflow_id)
            }
            
            # 4. Persistence
            msg_id = await redis_event_store.add_event(str(current_workflow_id), out_event)
            out_event["message_id"] = msg_id
            
            # 5. Streaming
            await websocket.send_json(out_event)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})

