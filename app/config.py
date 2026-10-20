"""
Application Configuration Module using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "CogniStudy Pro"
    APP_VERSION: str = "3.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Security
    API_KEY: Optional[str] = None
    CORS_ORIGINS: List[str] = ["*"]

    # LLM Providers & Keys
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "openai"  # openai, groq, anthropic, ollama, mock
    DEFAULT_MODEL_NAME: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 1500

    # Embeddings
    EMBEDDING_PROVIDER: str = "openai"  # openai, mock
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Vector Store & Storage
    INDEX_STORAGE_DIR: str = "faiss_data"
    DEFAULT_INDEX_DIR: str = "."
    MAX_UPLOAD_SIZE_MB: int = 50
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    DEFAULT_SEARCH_K: int = 4

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_WEBHOOK_URL: Optional[str] = None

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
