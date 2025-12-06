from sqlalchemy.orm import Session
from auth_service.app.core.security import create_access_token
from auth_service.app.services.user_service import authenticate_user


def login(db: Session, username: str, password: str):
    user = authenticate_user(db, username, password)
    if not user:
        return None

    token = create_access_token({"sub": str(user.id)})
    return token
