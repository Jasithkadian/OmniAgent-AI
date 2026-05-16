import hashlib
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class DocumentChunk(BaseModel):
    text: str
    metadata: Dict[str, Any]
    chunk_index: int
    chunk_hash: str = Field(description="Deterministic hash of content and metadata")

class SemanticChunker:
    """
    Production-grade chunker using RecursiveCharacterTextSplitter.
    Implements deterministic hashing and standardized metadata.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def split_text(self, text: str, base_metadata: Dict[str, Any]) -> List[DocumentChunk]:
        logger.info(f"Chunking document {base_metadata.get('document_id')} into size {self.chunk_size}")
        
        # 1. Split text into raw chunks
        raw_chunks = self.splitter.split_text(text)
        
        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            # 2. Prepare standardized metadata
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_size": len(chunk_text),
            })
            
            # 3. Generate deterministic hash (SHA256)
            # We hash the text and a subset of stable metadata to prevent duplicates
            hash_payload = {
                "text": chunk_text,
                "document_id": str(base_metadata.get("document_id")),
                "chunk_index": i
            }
            chunk_hash = hashlib.sha256(json.dumps(hash_payload, sort_keys=True).encode()).hexdigest()
            
            chunks.append(DocumentChunk(
                text=chunk_text,
                metadata=chunk_metadata,
                chunk_index=i,
                chunk_hash=chunk_hash
            ))
            
        logger.info(f"Created {len(chunks)} chunks for document {base_metadata.get('document_id')}")
        return chunks
