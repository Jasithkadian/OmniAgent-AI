import sys
import os
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
import json
from fastapi import WebSocket
import asyncio

from app.db.models import Workflow, WorkflowStatusEnum

# We need to import the LangGraph graph
# To ensure the backend can import the agents correctly if they are in the parent directory:
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
try:
    from agents import veyra_graph
except ImportError:
    # Fallback if running from a different root
    veyra_graph = None

class WorkflowService:
    @staticmethod
    async def create_workflow(db: AsyncSession, objective: str, user_id: UUID) -> Workflow:
        workflow = Workflow(
            user_id=user_id,
            objective=objective,
            status=WorkflowStatusEnum.queued
        )
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)
        return workflow

    @staticmethod
    async def run_workflow(db: AsyncSession, workflow_id: UUID, document_ids: Optional[list[UUID]] = None) -> Workflow:
        workflow = await db.get(Workflow, workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")
            
        workflow.status = WorkflowStatusEnum.running
        await db.commit()
        
        if veyra_graph:
...
