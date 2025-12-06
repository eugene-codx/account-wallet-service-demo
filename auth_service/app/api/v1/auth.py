from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth_service.app.db.database import get_db
from auth_service.app.schemas.auth import LoginRequest, Token
from auth_service.app.services.auth_service import login


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    token = login(db, data.username, data.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return Token(access_token=token)
