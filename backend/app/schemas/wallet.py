import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.credit_transaction import CreditTransactionKind


class WalletBalanceOut(BaseModel):
    balance: Decimal


class CreditTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: CreditTransactionKind
    amount: Decimal
    bet_id: uuid.UUID | None
    created_at: datetime


class CreditTransactionPage(BaseModel):
    items: list[CreditTransactionOut]
    total: int
    page: int
    page_size: int
