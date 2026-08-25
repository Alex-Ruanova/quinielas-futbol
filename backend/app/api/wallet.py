from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import require_current_user
from app.db.session import get_session
from app.models.credit_transaction import CreditTransaction
from app.models.user import User
from app.schemas.wallet import (
    CreditTransactionOut,
    CreditTransactionPage,
    WalletBalanceOut,
)
from app.services.wallet import get_balance

router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])


@router.get("", response_model=WalletBalanceOut)
def get_wallet(
    user: Annotated[User, Depends(require_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WalletBalanceOut:
    return WalletBalanceOut(balance=get_balance(session, user.id))


@router.get("/transactions", response_model=CreditTransactionPage)
def list_transactions(
    user: Annotated[User, Depends(require_current_user)],
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CreditTransactionPage:
    total = session.scalar(
        select(func.count())
        .select_from(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
    )
    rows = session.scalars(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .order_by(CreditTransaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return CreditTransactionPage(
        items=[CreditTransactionOut.model_validate(row) for row in rows],
        total=total or 0,
        page=page,
        page_size=page_size,
    )
