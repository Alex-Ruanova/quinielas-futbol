from datetime import datetime

from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.errors import AlreadySettled, InvalidSelection
from app.engine.resolution import BetInput, MatchResult, resolve_bet
from app.engine.resolution import Goal as EngineGoal
from app.engine.scoring import Score, ScoringRules, score_prediction
from app.engine.selection import Selection
from app.models.bet import Bet, BetStatus
from app.models.credit_transaction import CreditTransactionKind
from app.models.goal import Goal
from app.models.match import Match, MatchStatus
from app.models.prediction import Prediction
from app.models.round import Round
from app.models.season import Season
from app.services import wallet

_SELECTION_ADAPTER: TypeAdapter[Selection] = TypeAdapter(Selection)


def _season_for_match(session: Session, match: Match) -> Season:
    round_ = session.get(Round, match.round_id)
    if round_ is None:
        raise InvalidSelection(f"round {match.round_id} not found")
    season = session.get(Season, round_.season_id)
    if season is None:
        raise InvalidSelection(f"season {round_.season_id} not found")
    return season


def _match_result(session: Session, match: Match) -> MatchResult:
    if match.home_score is None or match.away_score is None:
        raise InvalidSelection(f"match {match.id} has no recorded result")
    goals = session.scalars(select(Goal).where(Goal.match_id == match.id))
    return MatchResult(
        home_score=match.home_score,
        away_score=match.away_score,
        goals=[
            EngineGoal(team_id=g.team_id, minute=g.minute, is_stoppage=g.is_stoppage)
            for g in goals
        ],
    )


def _scoring_rules(season: Season) -> ScoringRules:
    try:
        return ScoringRules.from_config(season.scoring_config)
    except ValidationError as exc:
        raise InvalidSelection(f"scoring_config invalido: {exc}") from exc


def settle_match(session: Session, match: Match, now: datetime) -> None:
    result = _match_result(session, match)

    pending_bets = session.scalars(
        select(Bet)
        .where(Bet.match_id == match.id, Bet.status == BetStatus.PENDING)
        .with_for_update()
    ).all()

    for bet in pending_bets:
        selection = _SELECTION_ADAPTER.validate_python(bet.selection)
        outcome = resolve_bet(
            BetInput(
                selection=selection, stake=bet.stake, odds_snapshot=bet.odds_snapshot
            ),
            result,
        )
        bet.status = BetStatus(outcome.status)
        bet.settled_at = now
        if outcome.status == "WON":
            wallet.credit(
                session,
                bet.user_id,
                outcome.payout,
                CreditTransactionKind.PAYOUT,
                bet_id=bet.id,
            )

    season = _season_for_match(session, match)
    rules = _scoring_rules(season)
    actual = Score(home=result.home_score, away=result.away_score)
    predictions = session.scalars(
        select(Prediction).where(Prediction.match_id == match.id)
    )
    for prediction in predictions:
        predicted = Score(
            home=prediction.predicted_home_score, away=prediction.predicted_away_score
        )
        prediction.points_awarded = score_prediction(predicted, actual, rules)

    match.settled_at = now
    session.flush()


def cancel_match(session: Session, match: Match, now: datetime) -> None:
    if match.status == MatchStatus.CANCELLED:
        raise AlreadySettled(f"match {match.id} is already cancelled")

    pending_bets = session.scalars(
        select(Bet)
        .where(Bet.match_id == match.id, Bet.status == BetStatus.PENDING)
        .with_for_update()
    ).all()

    for bet in pending_bets:
        wallet.credit(
            session,
            bet.user_id,
            bet.stake,
            CreditTransactionKind.REFUND,
            bet_id=bet.id,
        )
        bet.status = BetStatus.VOID
        bet.settled_at = now

    match.status = MatchStatus.CANCELLED
    match.settled_at = now
    session.flush()
