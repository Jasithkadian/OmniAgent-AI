import hashlib
import logging
from pathlib import Path
from uuid import UUID, uuid4
from typing import Optional

from fastapi import UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.db.models import Document, DocumentStatus
from app.schemas.documents import DocumentIngestResponse, DocumentSearchRequest, DocumentSearchResponse
from app.worker import celery_app
from rag.retrieval.hybrid_search import HybridSearchService
from rag.store.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    async def ingest_upload(
        self,
        file: UploadFile,
        user_id: UUID,
        conversation_id: Optional[UUID],
    ) -> DocumentIngestResponse:
        """
        Handles document upload, persistence, and enqueues background processing.
        Returns a 202 Accepted status to the client.
        """
        if self.session is None:
            raise AppError("Database session is required for ingestion.")

        payload = await file.read()
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(payload) > max_bytes:
            raise AppError(f"File exceeds {settings.max_upload_mb} MB limit.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".pdf", ".docx", ".txt"}:
            raise AppError("Only PDF, DOCX and TXT files are supported.")

        checksum = hashlib.sha256(payload).hexdigest()
        storage_path = self._persist_upload(payload, suffix)

        # Create document record in 'processing' status
        document = Document(
            user_id=user_id,
            conversation_id=conversation_id,
            filename=storage_path.name,
            original_filename=file.filename or storage_path.name,
            mime_type=file.content_type or "application/octet-stream",
            storage_url=str(storage_path),
            checksum=checksum,
            status=DocumentStatus.processing,
        )
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)

        # Dispatch background task for heavy RAG processing
        try:
            celery_app.send_task(
                "ingest_document_task",
                args=[str(storage_path), str(user_id), str(document.id)]
            )
            logger.info(f"Dispatched ingestion task for document {document.id}")
        except Exception as e:
            logger.error(f"Failed to dispatch Celery task: {e}")
            # Fallback: mark as failed if we can't even enqueue
            document.status = DocumentStatus.failed
            document.error_message = f"Background task dispatch failed: {str(e)}"
            await self.session.commit()

        return DocumentIngestResponse(
            document_id=document.id,
            status=document.status.value,
            chunk_count=0,
            token_count=0,
        )

    async def search(self, user_id: UUID, request: DocumentSearchRequest) -> DocumentSearchResponse:
        search_service = HybridSearchService(ChromaVectorStore())
        hits = await search_service.search(
            user_id=user_id,
            query=request.query,
            limit=request.limit,
            document_ids=request.document_ids,
        )
        return DocumentSearchResponse(query=request.query, hits=hits)

    def _persist_upload(self, payload: bytes, suffix: str) -> Path:
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        path = upload_dir / f"{uuid4()}{suffix}"
        path.write_bytes(payload)
        return path
