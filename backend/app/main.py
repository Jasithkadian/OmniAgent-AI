import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import APIException, api_exception_handler, unhandled_exception_handler
from app.api.v1.router import api_router
from app.db.session import engine, dispose_engine
from app.db.base import Base

logger = logging.getLogger(__name__)

async def verify_infrastructure():
    """Verify all critical infrastructure is reachable."""
    logger.info("Verifying infrastructure connectivity...")
    
    # 1. Database (PostgreSQL)
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("PostgreSQL connectivity verified.")
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        raise RuntimeError("Could not connect to PostgreSQL database.") from e

    # 2. Redis
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        logger.info("Redis connectivity verified.")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise RuntimeError("Could not connect to Redis.") from e

    # 3. Vector DB (Chroma)
    try:
        import chromadb
        # Simple client check
        client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        client.heartbeat()
        logger.info("ChromaDB connectivity verified.")
    except Exception as e:
        logger.error(f"ChromaDB initialization failed: {e}")
        # Not raising here as it might be a new install where dir doesn't exist yet
        # but we should at least log it.
        logger.warning("ChromaDB is not fully ready or directory is missing.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup structured logging
    setup_logging()
    
    # Run diagnostics
    await verify_infrastructure()
    
    # Initialize database tables (In prod, use Alembic migrations instead)
    async with engine.begin() as conn:
        
    yield
    
    # Teardown logic
    await dispose_engine()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
