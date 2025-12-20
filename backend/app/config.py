from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://journalbuddy:journalbuddy@localhost:5432/journalbuddy"

    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    deepgram_api_key: str = ""
    cartesia_api_key: str = ""
    cartesia_voice_id: str = "a0e99841-438c-4a64-b679-ae501e7d6091"  # Default friendly voice

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
