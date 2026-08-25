import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.engine.errors import InsufficientCredits
from app.models.credit_transaction import CreditTransaction, CreditTransactionKind
from app.models.user import User

_ZERO = Decimal("0.00")


def get_balance(session: Session, user_id: uuid.UUID) -> Decimal:
    total = session.scalar(
        select(func.coalesce(func.sum(CreditTransaction.amount), _ZERO)).where(
            CreditTransaction.user_id == user_id
        )
    )
    return Decimal(total) if total is not None else _ZERO


def post_transaction(
    session: Session,
    user_id: uuid.UUID,
    kind: CreditTransactionKind,
    amount: Decimal,
    bet_id: uuid.UUID | None = None,
) -> CreditTransaction:
    transaction = CreditTransaction(
        user_id=user_id, kind=kind, amount=amount, bet_id=bet_id
    )
    session.add(transaction)
    session.flush()
    return transaction


def debit(
    session: Session,
    user_id: uuid.UUID,
    amount: Decimal,
    bet_id: uuid.UUID | None = None,
) -> CreditTransaction:
    session.execute(select(User).where(User.id == user_id).with_for_update())
    balance = get_balance(session, user_id)
    if balance - amount < _ZERO:
        raise InsufficientCredits(
            f"Balance insuficiente: {balance} disponible, {amount} solicitado"
        )
    return post_transaction(
        session, user_id, CreditTransactionKind.STAKE, -amount, bet_id=bet_id
    )


def credit(
    session: Session,
    user_id: uuid.UUID,
    amount: Decimal,
    kind: CreditTransactionKind,
    bet_id: uuid.UUID | None = None,
) -> CreditTransaction:
    return post_transaction(session, user_id, kind, amount, bet_id=bet_id)
