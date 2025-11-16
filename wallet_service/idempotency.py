# wallet_service/idempotency.py
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from . import models, crud
from .database import SessionLocal

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE"]:
            idempotency_key = request.headers.get("Idempotency-Key")
            if idempotency_key:
                db = SessionLocal()
                existing_tx = crud.get_transaction_by_idempotency_key(db, idempotency_key)
                if existing_tx:
                    return Response(content="Idempotent request already processed", status_code=200)
                # Proceed and store after
        response = await call_next(request)
        # After successful, store if needed
        return response