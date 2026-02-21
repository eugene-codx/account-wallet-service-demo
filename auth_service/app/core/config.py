from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "auth-service"

    POSTGRES_USER: str = "User"
    POSTGRES_PASSWORD: str = Field(..., min_length=8)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "auth_db"

    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    UVICORN_PORT: str = "8001"

    class Config:
        base_dir = Path(__file__).resolve().parents[2]
        env_file = str(base_dir / ".env")


settings = Settings()

# Get the database URL
database_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
