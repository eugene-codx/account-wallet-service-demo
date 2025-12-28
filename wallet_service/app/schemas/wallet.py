from pydantic import BaseModel
from typing import Optional


class WalletBase(BaseModel):
    balance: float = 0.0


class WalletCreate(WalletBase):
    pass


class WalletResponse(WalletBase):
    id: int
    user_id: int
