from app.core.security import create_access_token
from app.services.user_service import authenticate_user
from sqlalchemy.ext.asyncio import AsyncSession


async def login(db: AsyncSession, username: str, password: str):
    user = await authenticate_user(db, username, password)
    if not user:
        return None

    token = create_access_token({"sub": str(user.id)})
    return token
