from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth_service.app.db.database import get_db
from auth_service.app.schemas.user import UserCreate, User
from auth_service.app.services.user_service import create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)
