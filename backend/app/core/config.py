from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, AnyHttpUrl
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Veyra Backend"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # Configurable in prod

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/veyra"
    redis_url: str = "redis://localhost:6379/0"

    # Authentication (Dev Placeholders)
    auth_dev_user_id: str = "00000000-0000-0000-0000-000000000000"
    auth_dev_email: str = "dev@veyra.ai"

    # File Uploads
    upload_dir: str = "var/uploads"
    max_upload_mb: int = 20

    # Vector DB (Chroma)
    chroma_db_dir: str = "var/chroma"
    chroma_collection_name: str = "veyra_knowledge"

    # Retrieval Settings
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.3
    max_context_chunks: int = 10

    # LLM Settings
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    model_config = SettingsConfigDict(case_sensitive=False, env_file=".env", extra="ignore")

settings = Settings()
