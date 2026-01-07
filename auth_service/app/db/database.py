from app.core.config import database_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

engine = create_async_engine(
    database_url,
    pool_pre_ping=True,
    echo=False,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db():
    async with async_session() as session:
        yield session
