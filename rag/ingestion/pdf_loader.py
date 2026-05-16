import asyncio
from typing import List, Dict, Any
import fitz  # PyMuPDF
from pydantic import BaseModel
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class DocumentExtract(BaseModel):
    text: str
    metadata: Dict[str, Any]

class PDFLoader:
    """
    Production-grade PDF loader using PyMuPDF.
    Extracts text page-by-page and preserves metadata.
    """
    def __init__(self):
        pass

    async def load_async(self, file_path: str, user_id: str, document_id: str) -> DocumentExtract:
        logger.info(f"Loading PDF with PyMuPDF: {file_path}")
        
        # Run sync PDF parsing in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._load_sync, file_path, user_id, document_id)

    def _load_sync(self, file_path: str, user_id: str, document_id: str) -> DocumentExtract:
        try:
            doc = fitz.open(file_path)
            full_text = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                # We can store text per page or joined. 
                # For basic RAG, we'll join but keep track of page count.
                full_text.append(text)
                
            metadata = {
                "source": file_path,
                "document_id": str(document_id),
                "user_id": str(user_id),
                "file_type": "pdf",
                "page_count": len(doc),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "ingestion_version": "1.0"
            }
            
            doc.close()
            return DocumentExtract(text="\n\n".join(full_text), metadata=metadata)
            
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise RuntimeError(f"Corrupted or invalid PDF file: {file_path}") from e
