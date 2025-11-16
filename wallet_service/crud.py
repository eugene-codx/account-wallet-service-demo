from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

def create_account(db: Session, account: schemas.AccountCreate, user_id: int):
    db_account = models.Account(name=account.name, user_id=user_id)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def create_transaction(db: Session, transaction: schemas.TransactionCreate, user_id: int, type: models.TransactionType):
    # Check limits, etc.; simplified
    account = db.query(models.Account).filter(models.Account.user_id == user_id).first()  # Assume one account for simplicity
    db_tx = models.Transaction(
        account_id=account.id,
        type=type,
        amount=transaction.amount,
        idempotency_key=transaction.idempotency_key,
        counterparty_account_id=transaction.counterparty_account_id
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

def get_balance(db: Session, account_id: int, user_id: int, at_time: str = None):
    query = db.query(func.sum(models.Transaction.amount)).filter(models.Transaction.account_id == account_id, models.Transaction.status == models.TransactionStatus.SETTLED)
    if at_time:
        query = query.filter(models.Transaction.timestamp <= datetime.fromisoformat(at_time))
    return query.scalar() or 0.0

def get_transaction_by_idempotency_key(db: Session, key: str):
    return db.query(models.Transaction).filter(models.Transaction.idempotency_key == key).first()

def settle_transaction(tx_id: int):
    db = database.SessionLocal()
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if tx:
        tx.status = models.TransactionStatus.SETTLED
        account = db.query(models.Account).filter(models.Account.id == tx.account_id).first()
        if tx.type in [models.TransactionType.DEPOSIT, models.TransactionType.TRANSFER_IN]:
            account.balance += tx.amount
        else:
            account.balance -= tx.amount
        db.commit()