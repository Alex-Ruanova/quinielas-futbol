from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .bands import band_for_minute
from .selection import Selection

CENTS = Decimal("0.01")


class Goal(BaseModel):
    model_config = ConfigDict(frozen=True)

    team_id: UUID
    minute: int
    is_stoppage: bool = False


class MatchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    home_score: int
    away_score: int
    goals: list[Goal] = []


class BetInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    selection: Selection
    stake: Decimal
    odds_snapshot: Decimal


class BetOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["WON", "LOST", "VOID"]
    payout: Decimal


def _outcome_winner(result: MatchResult) -> str:
    if result.home_score > result.away_score:
        return "HOME"
    if result.away_score > result.home_score:
        return "AWAY"
    return "DRAW"


def _won_outcome(bet: BetInput, result: MatchResult) -> bool:
    assert bet.selection.market == "OUTCOME"
    return bet.selection.pick == _outcome_winner(result)


def _won_goal_band(bet: BetInput, result: MatchResult) -> bool:
    assert bet.selection.market == "GOAL_BAND"
    selection = bet.selection
    return any(
        band_for_minute(goal.minute, goal.is_stoppage) == selection.band
        and (selection.team_id is None or goal.team_id == selection.team_id)
        for goal in result.goals
    )


def resolve_bet(bet: BetInput, result: MatchResult) -> BetOutcome:
    if bet.selection.market == "OUTCOME":
        won = _won_outcome(bet, result)
    else:
        won = _won_goal_band(bet, result)

    if not won:
        return BetOutcome(status="LOST", payout=Decimal("0.00"))

    payout = (bet.stake * bet.odds_snapshot).quantize(CENTS, rounding=ROUND_HALF_UP)
    return BetOutcome(status="WON", payout=payout)
