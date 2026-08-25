import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.engine.bands import GoalBand
from app.engine.config import DEFAULT_GOAL_BAND_ODDS
from app.engine.errors import (
    BettingClosed,
    InsufficientCredits,
    InvalidSelection,
    NotFound,
)
from app.engine.odds import OddsConfig, compute_odds
from app.engine.rules import is_open_for_betting, validate_stake
from app.engine.selection import Selection
from app.models.bet import Bet, BetMarket, BetStatus
from app.models.match import Match, MatchStatus
from app.models.prediction import Prediction
from app.models.round import Round
from app.models.season import Season
from app.models.team import Team
from app.services import wallet


def _get_match(session: Session, match_id: uuid.UUID) -> Match:
    match = session.get(Match, match_id)
    if match is None:
        raise NotFound(f"match {match_id} not found")
    return match


def _get_season_for_match(session: Session, match: Match) -> Season:
    round_ = session.get(Round, match.round_id)
    if round_ is None:
        raise NotFound(f"round {match.round_id} not found")
    season = session.get(Season, round_.season_id)
    if season is None:
        raise NotFound(f"season {round_.season_id} not found")
    return season


def _goal_band_odds(season: Season, band: str) -> Decimal:
    config = season.scoring_config or {}
    raw_map = config.get("goal_band_odds") if isinstance(config, dict) else None
    if isinstance(raw_map, dict) and band in raw_map:
        return Decimal(str(raw_map[band]))
    return DEFAULT_GOAL_BAND_ODDS


def _odds_for_selection(
    session: Session, match: Match, selection: Selection
) -> Decimal:
    if selection.market == "OUTCOME":
        home = session.get(Team, match.home_team_id)
        away = session.get(Team, match.away_team_id)
        if home is None or away is None:
            raise NotFound("team not found for match")
        odds = compute_odds(home.strength, away.strength, OddsConfig())
        return {
            "HOME": odds.odds_home,
            "DRAW": odds.odds_draw,
            "AWAY": odds.odds_away,
        }[selection.pick]

    season = _get_season_for_match(session, match)
    return _goal_band_odds(season, selection.band.value)


def place_bet(
    session: Session,
    user_id: uuid.UUID,
    match_id: uuid.UUID,
    selection: Selection,
    stake: Decimal,
    now: datetime,
) -> Bet:
    match = _get_match(session, match_id)
    if not is_open_for_betting(match.kickoff_at, now):
        raise BettingClosed(f"match {match_id} is closed for betting")
    validate_stake(stake)

    if (
        selection.market == "GOAL_BAND"
        and selection.team_id is not None
        and selection.team_id not in (match.home_team_id, match.away_team_id)
    ):
        raise InvalidSelection(
            f"team {selection.team_id} does not play in match {match_id}"
        )

    odds_snapshot = _odds_for_selection(session, match, selection)

    bet = Bet(
        id=uuid.uuid4(),
        user_id=user_id,
        match_id=match_id,
        market=BetMarket(selection.market),
        selection=selection.model_dump(mode="json"),
        stake=stake,
        odds_snapshot=odds_snapshot,
        status=BetStatus.PENDING,
    )
    session.add(bet)
    session.flush()

    try:
        wallet.debit(session, user_id, stake, bet_id=bet.id)
    except InsufficientCredits:
        session.delete(bet)
        session.flush()
        raise

    return bet


def list_bets(
    session: Session, user_id: uuid.UUID, status: BetStatus | None = None
) -> list[Bet]:
    stmt = select(Bet).where(Bet.user_id == user_id).order_by(Bet.created_at.desc())
    if status is not None:
        stmt = stmt.where(Bet.status == status)
    return list(session.scalars(stmt))


def list_bets_with_match(
    session: Session, user_id: uuid.UUID, status: BetStatus | None = None
) -> list[tuple[Bet, Match, str, str]]:
    """Apuestas del usuario con el contexto del partido, incluidos los ya liquidados.

    `/matches/upcoming` solo devuelve partidos futuros, asi que el historial no
    tiene de donde sacar los nombres de los equipos sin este join.
    """
    home = aliased(Team)
    away = aliased(Team)
    stmt = (
        select(Bet, Match, home.name, away.name)
        .join(Match, Match.id == Bet.match_id)
        .join(home, home.id == Match.home_team_id)
        .join(away, away.id == Match.away_team_id)
        .where(Bet.user_id == user_id)
        .order_by(Bet.created_at.desc())
    )
    if status is not None:
        stmt = stmt.where(Bet.status == status)
    return [(b, m, h, a) for b, m, h, a in session.execute(stmt)]


def list_seasons(session: Session) -> list[Season]:
    """Temporadas visibles para cualquier usuario autenticado.

    El leaderboard necesita un `season_id` y `/admin/seasons` exige is_admin,
    asi que sin esto un jugador normal no puede llegar a su propia tabla.
    """
    return list(session.scalars(select(Season).order_by(Season.starts_on.desc())))


def upsert_prediction(
    session: Session,
    user_id: uuid.UUID,
    match_id: uuid.UUID,
    predicted_home_score: int,
    predicted_away_score: int,
    now: datetime,
) -> Prediction:
    match = _get_match(session, match_id)
    if not is_open_for_betting(match.kickoff_at, now):
        raise BettingClosed(f"match {match_id} is closed for predictions")

    prediction = session.scalar(
        select(Prediction).where(
            Prediction.user_id == user_id, Prediction.match_id == match_id
        )
    )
    if prediction is None:
        prediction = Prediction(
            user_id=user_id,
            match_id=match_id,
            predicted_home_score=predicted_home_score,
            predicted_away_score=predicted_away_score,
        )
        session.add(prediction)
    else:
        prediction.predicted_home_score = predicted_home_score
        prediction.predicted_away_score = predicted_away_score
    session.flush()
    return prediction


def list_upcoming_matches(
    session: Session, user_id: uuid.UUID, now: datetime
) -> list[dict[str, Any]]:
    matches = list(
        session.scalars(
            select(Match)
            .where(Match.status == MatchStatus.SCHEDULED, Match.kickoff_at > now)
            .order_by(Match.kickoff_at)
        )
    )
    if not matches:
        return []

    match_ids = [m.id for m in matches]
    team_ids = {m.home_team_id for m in matches} | {m.away_team_id for m in matches}
    teams = {
        t.id: t for t in session.scalars(select(Team).where(Team.id.in_(team_ids)))
    }
    round_ids = {m.round_id for m in matches}
    rounds = {
        r.id: r for r in session.scalars(select(Round).where(Round.id.in_(round_ids)))
    }
    season_ids = {r.season_id for r in rounds.values()}
    seasons = {
        s.id: s
        for s in session.scalars(select(Season).where(Season.id.in_(season_ids)))
    }

    predictions = {
        p.match_id: p
        for p in session.scalars(
            select(Prediction).where(
                Prediction.user_id == user_id, Prediction.match_id.in_(match_ids)
            )
        )
    }
    bets_by_match: dict[uuid.UUID, list[Bet]] = {}
    for bet in session.scalars(
        select(Bet).where(Bet.user_id == user_id, Bet.match_id.in_(match_ids))
    ):
        bets_by_match.setdefault(bet.match_id, []).append(bet)

    results: list[dict[str, Any]] = []
    for match in matches:
        home = teams[match.home_team_id]
        away = teams[match.away_team_id]
        odds = compute_odds(home.strength, away.strength, OddsConfig())
        season = seasons[rounds[match.round_id].season_id]
        band_odds = {
            band.value: _goal_band_odds(season, band.value) for band in GoalBand
        }
        results.append(
            {
                "id": match.id,
                "round_id": match.round_id,
                "home_team_id": match.home_team_id,
                "away_team_id": match.away_team_id,
                "home_team_name": home.name,
                "away_team_name": away.name,
                "kickoff_at": match.kickoff_at,
                "odds_home": odds.odds_home,
                "odds_draw": odds.odds_draw,
                "odds_away": odds.odds_away,
                "goal_band_odds": band_odds,
                "my_prediction": predictions.get(match.id),
                "my_bets": bets_by_match.get(match.id, []),
            }
        )
    return results
