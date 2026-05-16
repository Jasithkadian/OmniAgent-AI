import asyncio
from typing import List, Dict, Any, Optional
import logging
import chromadb
from chromadb.config import Settings as ChromaSettings

from rag.chunking.semantic_chunker import DocumentChunk
from rag.embeddings.factory import embedding_factory
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    """
    Production-grade wrapper for ChromaDB.
    Handles persistent storage, batch upserts, and semantic search.
    """
    def __init__(self, collection_name: Optional[str] = None, persist_directory: Optional[str] = None):
        self.collection_name = collection_name or settings.chroma_collection_name
        self.persist_directory = persist_directory or settings.chroma_db_dir
        
        # Initialize Persistent Client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        self._provider = embedding_factory.get_provider("gemini")
        logger.info(f"Initialized ChromaVectorStore with collection '{self.collection_name}' at {self.persist_directory}")

    async def add_chunks(self, chunks: List[DocumentChunk]):
        """
        Adds document chunks to the vector store with manual embedding generation.
        """
        if not chunks:
            return

        logger.info(f"Ingesting {len(chunks)} chunks into ChromaDB")
        
        # 1. Extract texts for batch embedding
        texts = [chunk.text for chunk in chunks]
        
        # 2. Generate embeddings via Provider (with batching and retries)
        embeddings = await self._provider.embed_documents(texts)
        
        # 3. Prepare data for Chroma
        ids = [chunk.chunk_hash for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Ensure all metadata values are Chroma-compatible (str, int, float, bool)
        for meta in metadatas:
            for k, v in meta.items():
                if not isinstance(v, (str, int, float, bool)):
                    meta[k] = str(v)

        # 4. Upsert into Chroma (Synchronous call, wrapped in executor)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=texts
            )
        )
        
        logger.info(f"Successfully upserted {len(chunks)} chunks.")

    async def search(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Performs semantic search using vector similarity.
        """
        logger.info(f"Performing semantic search for: '{query[:50]}...'")
        
        # 1. Embed query
        query_embedding = await self._provider.embed_query(query)
        
        # 2. Query Chroma
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
        )
        
        # 3. Format results
        formatted_results = []
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i]  # Convert distance to similarity score
                })
                
        logger.info(f"Found {len(formatted_results)} relevant chunks.")
        return formatted_results

    async def delete_document(self, document_id: str):
        """
        Deletes all chunks associated with a document_id.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.collection.delete(where={"document_id": document_id})
        )
        logger.info(f"Deleted document {document_id} from vector store.")
