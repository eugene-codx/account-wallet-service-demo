from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.auth import LoginRequest, Token
from app.services.auth_service import login


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login_user(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    token = await login(db, data.username, data.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return Token(access_token=token)
