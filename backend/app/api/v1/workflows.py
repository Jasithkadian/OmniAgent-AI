import json
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from agents.core.graph import omniagent_graph
from agents.core.state import create_initial_state
from agents.core.memory import workspace_memory
from uuid import uuid4
from app.core.config import settings

from app.core.security import Principal, require_principal
from app.schemas.workflows import WorkflowRunRequest, WorkflowRunResponse
from app.services.workflows import WorkflowService

router = APIRouter()


@router.post("/run", response_model=WorkflowRunResponse)
async def run_workflow(
    request: WorkflowRunRequest,
    principal: Principal = Depends(require_principal),
) -> WorkflowRunResponse:
    return await WorkflowService().run(user_id=principal.user_id, request=request)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        payload = json.loads(data)
        
        user_id = UUID(settings.auth_dev_user_id)
        
        objective = payload.get("objective")
        document_ids = payload.get("document_ids", [])
        
        state = create_initial_state(
            workflow_id=uuid4(),
            user_id=user_id,
            conversation_id=None,
            objective=objective,
            document_ids=document_ids,
        )
        state = workspace_memory.hydrate(state)
        
        # Stream events using langgraph v2 streaming
        async for event in omniagent_graph.graph.astream_events(state, version="v2"):
            # We serialize state output properly, skipping complex objects if needed
            # For logging purposes we just need name and event type
            await websocket.send_json({
                "event": event["event"],
                "name": event["name"]
            })
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})

