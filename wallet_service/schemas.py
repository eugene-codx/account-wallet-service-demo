from pydantic import BaseModel
from datetime import datetime

class AccountCreate(BaseModel):
    name: str

class Account(AccountCreate):
    id: int
    balance: float

class TransactionCreate(BaseModel):
    amount: float
    idempotency_key: str
    counterparty_account_id: int | None = None

class Transaction(TransactionCreate):
    id: int
    type: str
    status: str
    timestamp: datetime