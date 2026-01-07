import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.db.database import Base
from sqlalchemy import UUID, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    idempotency_key: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # DEPOSIT, WITHDRAW, TRANSFER_OUT, TRANSFER_IN
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
