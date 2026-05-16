from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from app.schemas.health import HealthResponse
from app.db.session import get_session
from app.core.config import settings
from app.core.observability import obs_manager
from rag.embeddings.factory import embedding_factory

router = APIRouter()

@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check to verify API is responsive."""
    return HealthResponse(status="ok")

@router.get("/db", response_model=HealthResponse)
async def health_db(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    """Check connectivity to PostgreSQL."""
    try:
        await session.execute(text("SELECT 1"))
        return HealthResponse(status="ok")
    except Exception as e:
        return HealthResponse(status=f"error: {str(e)}")

@router.get("/redis", response_model=HealthResponse)
async def health_redis() -> HealthResponse:
    """Check connectivity to Redis."""
    try:
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        return HealthResponse(status="ok")
    except Exception as e:
        return HealthResponse(status=f"error: {str(e)}")

@router.get("/embeddings", response_model=HealthResponse)
async def health_embeddings() -> HealthResponse:
    """Check connectivity to Embedding Provider (e.g., Gemini)."""
    try:
        provider = embedding_factory.get_provider("gemini")
        # Attempt a tiny test embedding
        await provider.embed_query("health check")
        return HealthResponse(status="ok")
    except Exception as e:
        return HealthResponse(status=f"error: {str(e)}")

@router.get("/vectorstore", response_model=HealthResponse)
async def health_vectorstore() -> HealthResponse:
    """Check connectivity to ChromaDB."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        client.heartbeat()
        return HealthResponse(status="ok")
    except Exception as e:
        return HealthResponse(status=f"error: {str(e)}")

@router.get("/metrics")
async def get_metrics():
    """Get aggregated platform performance metrics."""
    return obs_manager.get_summary_metrics()
