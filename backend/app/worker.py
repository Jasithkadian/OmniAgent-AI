import os
import asyncio
import logging
from celery import Celery
from uuid import UUID

# Ensure correct Python path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.core.config import settings

logger = logging.getLogger(__name__)

# Setup Celery Application
celery_app = Celery(
    "veyra_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="ingest_document_task")
def ingest_document_task(file_path: str, user_id: str, document_id: str):
    """
    Background worker task to process heavy RAG chunking and embedding.
    Updates the database status upon completion.
    """
    try:
        from rag.ingestion.pipeline import rag_pipeline
        from app.db.session import AsyncSessionLocal
        from app.db.models.documents import Document, DocumentStatus
        
        async def _run_ingestion():
            # 1. Execute RAG pipeline
            result = await rag_pipeline.ingest_document(
                file_path=file_path, 
                user_id=UUID(user_id), 
                document_id=UUID(document_id)
            )
            
            # 2. Update Database Status
            async with AsyncSessionLocal() as session:
                document = await session.get(Document, UUID(document_id))
                if document:
                    document.status = DocumentStatus.indexed
                    document.chunk_count = result.get("chunks_created", 0)
                    # In a full implementation, we would also sync chunks to SQL here
                    await session.commit()
            
            return result

        return asyncio.run(_run_ingestion())
        
    except Exception as e:
        logger.error(f"Ingestion task failed for {document_id}: {e}")
        # Try to mark as failed in DB
        try:
            from app.db.session import AsyncSessionLocal
            from app.db.models.documents import Document, DocumentStatus
            async def _mark_failed():
                async with AsyncSessionLocal() as session:
                    document = await session.get(Document, UUID(document_id))
                    if document:
                        document.status = DocumentStatus.failed
                        document.error_message = str(e)
                        await session.commit()
            asyncio.run(_mark_failed())
        except:
            pass
        return {"error": str(e)}
