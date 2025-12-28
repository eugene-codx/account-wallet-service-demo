from jose import jwt, exceptions
from fastapi import HTTPException, status
from app.core.config import settings


def verify_jwt(token: str) -> dict:
    """
    Локальная проверка JWT токена
    """

    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "").strip()

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
    except exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except exceptions.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return payload
