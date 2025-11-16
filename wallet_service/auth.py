# wallet_service/auth.py  # Integration module
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from auth_service.main import SECRET_KEY, ALGORITHM  # Shared secret; in prod use env or key service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth-service:8001/token")  # Point to auth service

async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # Fetch user_id from DB or cache; for simplicity assume we query
        from .database import SessionLocal
        db = SessionLocal()
        from auth_service import models, crud
        user = crud.get_user_by_username(db, username=username)
        if user is None:
            raise credentials_exception
        return user.id
    except JWTError:
        raise credentials_exception