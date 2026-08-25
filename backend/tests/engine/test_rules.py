from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.engine.errors import StakeOutOfRange
from app.engine.rules import is_open_for_betting, validate_stake


def test_is_open_for_betting_is_false_at_exact_kickoff() -> None:
    kickoff_at = datetime(2026, 1, 1, 18, 0, tzinfo=UTC)
    assert is_open_for_betting(kickoff_at, now=kickoff_at) is False


def test_is_open_for_betting_is_true_before_kickoff() -> None:
    kickoff_at = datetime(2026, 1, 1, 18, 0, tzinfo=UTC)
    now = kickoff_at - timedelta(minutes=1)
    assert is_open_for_betting(kickoff_at, now=now) is True


def test_validate_stake_rejects_below_minimum() -> None:
    with pytest.raises(StakeOutOfRange):
        validate_stake(Decimal("5.00"))


def test_validate_stake_rejects_above_maximum() -> None:
    with pytest.raises(StakeOutOfRange):
        validate_stake(Decimal("501.00"))


def test_validate_stake_accepts_boundaries() -> None:
    validate_stake(Decimal("10.00"))
    validate_stake(Decimal("500.00"))
