# config\settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Arbor AI Studio"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10

    # Redis
    REDIS_URL: str
    REDIS_TTL: int = 3600  # 1 hour (reduced from 1800 for better cleanup)

    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./data/images"

    # Supabase Storage
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_BUCKET_NAME: str = "arbor_images"

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Imagen
    IMAGEN_API_KEY: str
    IMAGEN_MODEL: str = "gemini-2.0-flash-exp"

    # Streamlit
    STREAMLIT_SERVER_PORT: int = 8501

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
