import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: list[str] = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "blockchain-events")
    KAFKA_GROUP_ID: str = os.getenv("KAFKA_GROUP_ID", "service-group")

    # Database settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "service")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD", None)

    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Proxy to allow fresh lookup after monkeypatching os.environ
class _SettingsProxy:
    def __getattr__(self, item: str):
        return getattr(Settings(), item)

settings = _SettingsProxy()


