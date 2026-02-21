import uuid
from typing import List

from app.core.config import settings
from app.db.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.schemas import (
    AccountResponse,
    DepositRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawRequest,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/wallet", tags=["wallet"])

security = HTTPBearer()


async def get_current_user_id(
    auth: HTTPAuthorizationCredentials = Depends(security),
) -> UUID4:
    try:
        token = auth.credentials
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("/accounts", response_model=List[AccountResponse])
async def list_accounts(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Account).where(Account.user_id == uuid.UUID(user_id))
    )
    return result.scalars().all()


@router.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_account(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    new_account = Account(user_id=uuid.UUID(user_id))
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return new_account


@router.post("/deposit")
async def deposit_funds(
    req: DepositRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Use FOR UPDATE to lock the account row
    res = await db.execute(
        select(Account).where(Account.id == req.account_id).with_for_update()
    )
    account = res.scalars().first()

    if not account or str(account.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Account not found")

    account.balance += req.amount
    db.add(
        Transaction(
            account_id=account.id,
            amount=req.amount,
            type="DEPOSIT",
            idempotency_key=req.idempotency_key,
        )
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Transaction already processed")
    await db.refresh(account)
    return {"status": "success", "new_balance": account.balance}


@router.post("/transfer")
async def transfer_funds(
    req: TransferRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Block both accounts in a consistent order to prevent deadlocks
    ids = sorted([req.from_account_id, req.to_account_id])
    res = await db.execute(select(Account).where(Account.id.in_(ids)).with_for_update())
    accounts = {str(a.id): a for a in res.scalars().all()}

    if len(accounts) < 2:
        raise HTTPException(status_code=404, detail="One or both accounts not found")

    sender = accounts[str(req.from_account_id)]
    receiver = accounts[str(req.to_account_id)]

    if str(sender.user_id) != str(user_id):
        raise HTTPException(
            status_code=403, detail="Forbidden: You don't own the source account"
        )

    if sender.balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    sender.balance -= req.amount
    receiver.balance += req.amount

    db.add(
        Transaction(
            account_id=sender.id,
            amount=-req.amount,
            type="TRANSFER_OUT",
            idempotency_key=req.idempotency_key,
        )
    )
    db.add(
        Transaction(
            account_id=receiver.id,
            amount=req.amount,
            type="TRANSFER_IN",
            idempotency_key=f"__internal__:tx:{req.idempotency_key}:in",
        )
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Transaction already processed")
    return {"status": "success", "new_balance": sender.balance}


@router.post("/withdraw")
async def withdraw_funds(
    req: WithdrawRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Withdraw funds from a user's account with idempotency check and row locking.
    """
    # 1. Block the account row and withdraw funds
    res = await db.execute(
        select(Account).where(Account.id == req.account_id).with_for_update()
    )
    account = res.scalars().first()

    if not account or str(account.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Account not found")

    if account.balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    account.balance -= req.amount
    db.add(
        Transaction(
            account_id=account.id,
            amount=-req.amount,
            type="WITHDRAW",
            idempotency_key=req.idempotency_key,
        )
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Transaction already processed")
    return {"status": "success", "new_balance": account.balance}


@router.get(
    "/accounts/{account_id}/transactions", response_model=List[TransactionResponse]
)
async def get_transaction_history(
    account_id: UUID4,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Getting transaction history for a specific account with pagination.
    """
    # First, verify that the account belongs to the user
    acc_check = await db.execute(
        select(Account).where(
            Account.id == account_id, Account.user_id == uuid.UUID(user_id)
        )
    )
    if not acc_check.scalars().first():
        raise HTTPException(status_code=403, detail="Access denied to this account")

    # Request transaction history with pagination, ordered by most recent first
    result = await db.execute(
        select(Transaction)
        .where(Transaction.account_id == account_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
