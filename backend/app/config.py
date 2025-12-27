from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core app
    APP_NAME: str = "Ariadne Metadata Management System"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str

    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    # Redis
    REDIS_URL: str

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # default 12 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    # Celery (phase 4+)
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # CORS
    CORS_ORIGINS: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Crypto
    ENCRYPTION_KEY: str | None = None
    BCRYPT_ROUNDS: int = 12

    # Performance tuning
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    REDIS_POOL_SIZE: int = 10

    # Oracle thick client (optional)
    ORACLE_CLIENT_LIB_DIR: str | None = "/Users/shenshunan/projects/Ariadne/tools/oracle"

    # LLM / AI
    LLM_PROVIDER: str = "deepseek"
    LLM_API_BASE: str = "https://api.deepseek.com"
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = "deepseek-chat"
    LLM_TIMEOUT: int = 30
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
