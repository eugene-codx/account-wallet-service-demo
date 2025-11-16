from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from .database import Base


class TransactionType(PyEnum):
    DEPOSIT = 'deposit'
    WITHDRAW = 'withdraw'
    TRANSFER_IN = 'transfer_in'
    TRANSFER_OUT = 'transfer_out'


class TransactionStatus(PyEnum):
    PENDING = 'pending'
    SETTLED = 'settled'
    FAILED = 'failed'


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # From auth_service
    name = Column(String, nullable=False)  # e.g., 'main', 'bonus'
    balance = Column(Float, default=0.0)  # For simplicity, but in prod use ledger sum

    transactions = relationship('Transaction', back_populates='account')


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    idempotency_key = Column(String, unique=True, nullable=False)
    counterparty_account_id = Column(Integer, ForeignKey('accounts.id'))  # For transfers

    account = relationship('Account', back_populates='transactions')