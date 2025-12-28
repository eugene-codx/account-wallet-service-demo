from sqlalchemy import Column, Integer, Numeric, ForeignKey
from app.db.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    balance = Column(Numeric(12, 2), default=0)
