from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.errors import InvalidSelection, NotFound
from app.engine.odds import MatchOdds, OddsConfig, compute_odds
from app.models.match import Match
from app.models.round import Round
from app.models.season import Season
from app.models.team import Team
from app.schemas.catalog import (
    MatchCreate,
    MatchUpdate,
    RoundCreate,
    RoundUpdate,
    ScoringConfigUpdate,
    SeasonCreate,
    SeasonUpdate,
    TeamCreate,
    TeamUpdate,
)


def create_team(session: Session, data: TeamCreate) -> Team:
    team = Team(**data.model_dump())
    session.add(team)
    session.flush()
    return team


def get_team(session: Session, team_id: UUID) -> Team:
    team = session.get(Team, team_id)
    if team is None:
        raise NotFound(f"team {team_id} not found")
    return team


def list_teams(session: Session) -> list[Team]:
    return list(session.scalars(select(Team).order_by(Team.name)))


def update_team(session: Session, team_id: UUID, data: TeamUpdate) -> Team:
    team = get_team(session, team_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    session.flush()
    return team


def delete_team(session: Session, team_id: UUID) -> None:
    team = get_team(session, team_id)
    session.delete(team)
    session.flush()


def create_season(session: Session, data: SeasonCreate) -> Season:
    season = Season(**data.model_dump())
    session.add(season)
    session.flush()
    return season


def get_season(session: Session, season_id: UUID) -> Season:
    season = session.get(Season, season_id)
    if season is None:
        raise NotFound(f"season {season_id} not found")
    return season


def list_seasons(session: Session) -> list[Season]:
    return list(session.scalars(select(Season).order_by(Season.starts_on)))


def update_season(session: Session, season_id: UUID, data: SeasonUpdate) -> Season:
    season = get_season(session, season_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(season, field, value)
    session.flush()
    return season


def delete_season(session: Session, season_id: UUID) -> None:
    season = get_season(session, season_id)
    session.delete(season)
    session.flush()


def update_scoring_config(
    session: Session, season_id: UUID, patch: ScoringConfigUpdate
) -> Season:
    season = get_season(session, season_id)
    config = dict(season.scoring_config or {})

    for field in ("outcome", "exact_score", "goal_band"):
        value = getattr(patch, field)
        if value is not None:
            config[field] = value

    if patch.goal_band_odds is not None:
        existing_odds = config.get("goal_band_odds")
        odds_map: dict[str, str] = (
            dict(existing_odds) if isinstance(existing_odds, dict) else {}
        )
        for band, odds in patch.goal_band_odds.items():
            odds_map[band.value] = str(odds)
        config["goal_band_odds"] = odds_map

    season.scoring_config = config
    session.flush()
    return season


def create_round(session: Session, data: RoundCreate) -> Round:
    round_ = Round(**data.model_dump())
    session.add(round_)
    session.flush()
    return round_


def get_round(session: Session, round_id: UUID) -> Round:
    round_ = session.get(Round, round_id)
    if round_ is None:
        raise NotFound(f"round {round_id} not found")
    return round_


def list_rounds(session: Session, season_id: UUID | None = None) -> list[Round]:
    stmt = select(Round).order_by(Round.number)
    if season_id is not None:
        stmt = stmt.where(Round.season_id == season_id)
    return list(session.scalars(stmt))


def update_round(session: Session, round_id: UUID, data: RoundUpdate) -> Round:
    round_ = get_round(session, round_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(round_, field, value)
    session.flush()
    return round_


def delete_round(session: Session, round_id: UUID) -> None:
    round_ = get_round(session, round_id)
    session.delete(round_)
    session.flush()


def _validate_match_window(
    home_team_id: UUID, away_team_id: UUID, kickoff_at: datetime, round_: Round
) -> None:
    if home_team_id == away_team_id:
        raise InvalidSelection("a team cannot play against itself")
    if not (round_.opens_at <= kickoff_at <= round_.closes_at):
        raise InvalidSelection(
            f"kickoff_at must be within [{round_.opens_at}, {round_.closes_at}]"
        )


def create_match(session: Session, data: MatchCreate) -> Match:
    round_ = get_round(session, data.round_id)
    _validate_match_window(
        data.home_team_id, data.away_team_id, data.kickoff_at, round_
    )
    match = Match(**data.model_dump())
    session.add(match)
    session.flush()
    return match


def get_match(session: Session, match_id: UUID) -> Match:
    match = session.get(Match, match_id)
    if match is None:
        raise NotFound(f"match {match_id} not found")
    return match


def list_matches(session: Session, round_id: UUID | None = None) -> list[Match]:
    stmt = select(Match).order_by(Match.kickoff_at)
    if round_id is not None:
        stmt = stmt.where(Match.round_id == round_id)
    return list(session.scalars(stmt))


def update_match(session: Session, match_id: UUID, data: MatchUpdate) -> Match:
    match = get_match(session, match_id)
    changes = data.model_dump(exclude_unset=True)

    home_team_id = changes.get("home_team_id", match.home_team_id)
    away_team_id = changes.get("away_team_id", match.away_team_id)
    kickoff_at = changes.get("kickoff_at", match.kickoff_at)
    round_id = changes.get("round_id", match.round_id)

    if {"home_team_id", "away_team_id", "kickoff_at", "round_id"} & changes.keys():
        round_ = get_round(session, round_id)
        _validate_match_window(home_team_id, away_team_id, kickoff_at, round_)

    for field, value in changes.items():
        setattr(match, field, value)
    session.flush()
    return match


def delete_match(session: Session, match_id: UUID) -> None:
    match = get_match(session, match_id)
    session.delete(match)
    session.flush()


def odds_preview(strength_home: int, strength_away: int) -> MatchOdds:
    return compute_odds(strength_home, strength_away, OddsConfig())


def team_odds_preview(
    session: Session, team_id: UUID, opponent_strength: int, strength: int | None = None
) -> MatchOdds:
    """`strength` simula una fuerza sin persistirla: el slider del panel previsualiza
    antes de guardar, y cambiar `team.strength` altera los momios en vivo de todos
    los partidos abiertos."""
    team = get_team(session, team_id)
    return odds_preview(
        strength if strength is not None else team.strength, opponent_strength
    )
