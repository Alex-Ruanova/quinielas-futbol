from decimal import Decimal
from uuid import uuid4

from app.engine.bands import GoalBand
from app.engine.resolution import BetInput, Goal, MatchResult, resolve_bet
from app.engine.selection import GoalBandSelection, OutcomeSelection


def test_goal_band_bet_on_away_team_loses_when_home_scores_in_band() -> None:
    home_id = uuid4()
    away_id = uuid4()

    bet = BetInput(
        selection=GoalBandSelection(band=GoalBand.MIN_0_15, team_id=away_id),
        stake=Decimal("50.00"),
        odds_snapshot=Decimal("4.50"),
    )
    result = MatchResult(
        home_score=1,
        away_score=0,
        goals=[Goal(team_id=home_id, minute=10, is_stoppage=False)],
    )

    outcome = resolve_bet(bet, result)

    assert outcome.status == "LOST"
    assert outcome.payout == Decimal("0.00")


def test_goal_band_bet_wins_when_specified_team_scores_in_band() -> None:
    home_id = uuid4()
    away_id = uuid4()

    bet = BetInput(
        selection=GoalBandSelection(band=GoalBand.MIN_0_15, team_id=home_id),
        stake=Decimal("50.00"),
        odds_snapshot=Decimal("4.50"),
    )
    result = MatchResult(
        home_score=1,
        away_score=0,
        goals=[Goal(team_id=home_id, minute=10, is_stoppage=False)],
    )

    outcome = resolve_bet(bet, result)

    assert outcome.status == "WON"
    assert outcome.payout == Decimal("225.00")


def test_outcome_bet_wins_on_correct_pick() -> None:
    bet = BetInput(
        selection=OutcomeSelection(pick="HOME"),
        stake=Decimal("100.00"),
        odds_snapshot=Decimal("1.80"),
    )
    result = MatchResult(home_score=2, away_score=0, goals=[])

    outcome = resolve_bet(bet, result)

    assert outcome.status == "WON"
    assert outcome.payout == Decimal("180.00")


def test_outcome_bet_loses_on_wrong_pick() -> None:
    bet = BetInput(
        selection=OutcomeSelection(pick="AWAY"),
        stake=Decimal("100.00"),
        odds_snapshot=Decimal("1.80"),
    )
    result = MatchResult(home_score=2, away_score=0, goals=[])

    outcome = resolve_bet(bet, result)

    assert outcome.status == "LOST"
    assert outcome.payout == Decimal("0.00")
