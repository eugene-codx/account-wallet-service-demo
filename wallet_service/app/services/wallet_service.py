from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import async_session
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate


class WalletService:

    @staticmethod
    async def create_wallet(user_id: int, data: WalletCreate):
        async with async_session() as session:  # type: AsyncSession
            wallet = Wallet(user_id=user_id, balance=data.balance)
            session.add(wallet)
            await session.commit()
            await session.refresh(wallet)
            return wallet

    @staticmethod
    async def get_wallet(user_id: int):
        async with async_session() as session:  # type: AsyncSession
            result = await session.execute(
                select(Wallet).where(Wallet.user_id == user_id)
            )
            wallet = result.scalar_one_or_none()
            return wallet
