# wallet_service/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, crud, database
from .idempotency import IdempotencyMiddleware
from .auth import get_current_user_id  # Integration with auth
from .worker import process_transaction  # For queue example

app = FastAPI()

app.add_middleware(IdempotencyMiddleware)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/accounts/", response_model=schemas.Account)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return crud.create_account(db=db, account=account, user_id=user_id)

@app.post("/transactions/deposit/")
def deposit(transaction: schemas.TransactionCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Simple example; enqueue for async
    tx = crud.create_transaction(db=db, transaction=transaction, user_id=user_id, type=models.TransactionType.DEPOSIT)
    process_transaction.delay(tx.id)  # RQ enqueue
    return {"status": "pending", "tx_id": tx.id}

# Similar for withdraw, transfer, etc.

@app.get("/balance/{account_id}")
def get_balance(account_id: int, at_time: str = None, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Logic to sum transactions up to at_time
    return crud.get_balance(db=db, account_id=account_id, user_id=user_id, at_time=at_time)