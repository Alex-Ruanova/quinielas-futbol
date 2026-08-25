from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.errors import InsufficientCredits
from app.models.credit_transaction import CreditTransaction, CreditTransactionKind
from app.services import users, wallet


def _register_user(session: Session, email: str = "wallet-user@example.com") -> object:
    return users.register(
        session,
        email=email,
        password="walletpass123",
        display_name="Wallet User",
    )


def test_register_creates_single_seed_transaction_with_1000_balance(
    session: Session,
) -> None:
    user = _register_user(session)

    transactions = session.scalars(
        select(CreditTransaction).where(CreditTransaction.user_id == user.id)
    ).all()
    assert len(transactions) == 1
    assert transactions[0].kind == CreditTransactionKind.SEED

    assert wallet.get_balance(session, user.id) == Decimal("1000.00")


def test_get_balance_sums_seed_stake_and_payout(session: Session) -> None:
    user = _register_user(session, email="ledger@example.com")

    wallet.post_transaction(
        session, user.id, CreditTransactionKind.STAKE, Decimal("-50.00")
    )
    wallet.post_transaction(
        session, user.id, CreditTransactionKind.PAYOUT, Decimal("150.00")
    )

    assert wallet.get_balance(session, user.id) == Decimal("1100.00")


def test_debit_more_than_balance_raises_and_does_not_insert(session: Session) -> None:
    user = _register_user(session, email="overdraft@example.com")

    with pytest.raises(InsufficientCredits):
        wallet.debit(session, user.id, Decimal("5000.00"))

    transactions = session.scalars(
        select(CreditTransaction).where(CreditTransaction.user_id == user.id)
    ).all()
    assert len(transactions) == 1
    assert wallet.get_balance(session, user.id) == Decimal("1000.00")
