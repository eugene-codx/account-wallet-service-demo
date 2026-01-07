import bcrypt
from app.models.user import User
from app.schemas.user import UserCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(db: AsyncSession, user: UserCreate):
    from fastapi import HTTPException

    existing = await db.execute(select(User).where(User.username == user.username))
    if existing.scalars().first():
        raise HTTPException(
            status_code=400, detail="User with this username already exists"
        )

    password_bytes = user.password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    db_user = User(username=user.username, hashed_password=hashed)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = (
        (await db.execute(select(User).where(User.username == username)))
        .scalars()
        .first()
    )

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
