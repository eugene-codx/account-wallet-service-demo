import logging

from app.api.v1 import wallet
from app.core.config import settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(wallet.router)

logger = logging.getLogger(settings.PROJECT_NAME)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Глобальный перехват ошибок БД.
    Позволяет не "светить" внутренности базы наружу, но логировать ошибку.
    """
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal database error. Please try again later."},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our side."},
    )
