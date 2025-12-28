from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "wallet-service"

    POSTGRES_USER: str = "User"
    POSTGRES_PASSWORD: str = "Password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "wallet_db"

    JWT_SECRET: str = "your_jwt_secret_key"

    UVICORN_PORT: str = "8002"

    class Config:
        base_dir = Path(__file__).resolve().parents[2]
        env_file = str(base_dir / ".env")


settings = Settings()

# Get the database URL
database_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"