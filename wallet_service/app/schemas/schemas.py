from datetime import datetime
from decimal import Decimal

from pydantic import UUID4, BaseModel, Field


class TransferRequest(BaseModel):
    from_account_id: UUID4
    to_account_id: UUID4
    amount: Decimal = Field(gt=0)
    idempotency_key: str


class DepositRequest(BaseModel):
    account_id: UUID4
    amount: Decimal = Field(gt=0)
    idempotency_key: str


class AccountResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    balance: Decimal
    currency: str

    class Config:
        from_attributes = True


class WithdrawRequest(BaseModel):
    account_id: UUID4
    amount: Decimal = Field(gt=0)
    idempotency_key: str


class TransactionResponse(BaseModel):
    id: UUID4
    account_id: UUID4
    amount: Decimal
    type: str
    created_at: datetime

    class Config:
        from_attributes = True
