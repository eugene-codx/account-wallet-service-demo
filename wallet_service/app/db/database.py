from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import database_url

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