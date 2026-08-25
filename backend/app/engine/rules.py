from datetime import datetime
from decimal import Decimal

from .config import MAX_STAKE, MIN_STAKE
from .errors import StakeOutOfRange


def is_open_for_betting(kickoff_at: datetime, now: datetime) -> bool:
    return now < kickoff_at


def validate_stake(stake: Decimal) -> None:
    if stake < MIN_STAKE or stake > MAX_STAKE:
        raise StakeOutOfRange(f"stake {stake} outside [{MIN_STAKE}, {MAX_STAKE}]")
