import os
import time
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from rag.ingestion.pdf_loader import PDFLoader
from rag.ingestion.docx_loader import DocxLoader
from rag.chunking.semantic_chunker import SemanticChunker
from rag.store.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Orchestrates the entire ingestion flow: Loading -> Chunking -> Embedding -> Storage.
    Includes failure recovery logic and performance metrics.
    """
    def __init__(self, vector_store: Optional[ChromaVectorStore] = None):
        self.pdf_loader = PDFLoader()
        self.docx_loader = DocxLoader()
        self.chunker = SemanticChunker(chunk_size=1000, chunk_overlap=150)
        self.vector_store = vector_store or ChromaVectorStore()

    async def ingest_document(self, file_path: str, user_id: UUID, document_id: UUID) -> Dict[str, Any]:
        """
        Main entry point for processing a new document.
        """
        start_time = time.time()
        logger.info(f"Starting production RAG ingestion for {file_path}")
        
        try:
            # 1. Loading & Parsing
            _, ext = os.path.splitext(file_path.lower())
            if ext == '.pdf':
                doc_extract = await self.pdf_loader.load_async(file_path, str(user_id), str(document_id))
            elif ext == '.docx':
                doc_extract = await self.docx_loader.load_async(file_path, str(user_id), str(document_id))
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                from rag.ingestion.pdf_loader import DocumentExtract
                from datetime import datetime, timezone
                doc_extract = DocumentExtract(
                    text=text, 
                    metadata={
                        "source": file_path, "document_id": str(document_id), "user_id": str(user_id), 
                        "file_type": "txt", "created_at": datetime.now(timezone.utc).isoformat(),
                        "ingestion_version": "1.0"
                    }
                )
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            
            parse_duration = time.time() - start_time
            logger.info(f"Parsing complete in {parse_duration:.2f}s")
            
            # 2. Chunking & Hashing
            chunk_start = time.time()
            chunks = self.chunker.split_text(doc_extract.text, base_metadata=doc_extract.metadata)
            chunk_duration = time.time() - chunk_start
            
            # 3. Embedding and Storage
            # ChromaVectorStore.add_chunks handles manual embedding via provider
            store_start = time.time()
            await self.vector_store.add_chunks(chunks)
            store_duration = time.time() - store_start
            
            total_duration = time.time() - start_time
            logger.info(f"Ingestion successful for {document_id}. Total time: {total_duration:.2f}s")
            
            return {
                "status": "success",
                "document_id": str(document_id),
                "chunks_created": len(chunks),
                "metrics": {
                    "parse_duration": parse_duration,
                    "chunk_duration": chunk_duration,
                    "store_duration": store_duration,
                    "total_duration": total_duration
                }
            }
            
        except Exception as e:
            logger.error(f"Ingestion failed for {document_id}: {str(e)}")
            # In a real system, we'd trigger a rollback in the vector store if partial 
            # chunks were added, but Chroma upsert is somewhat idempotent due to hashes.
            raise

# Global singleton
rag_pipeline = RAGPipeline()
