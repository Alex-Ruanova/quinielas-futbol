import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.errors import InvalidSelection, NotFound
from app.models.goal import Goal
from app.models.match import Match, MatchStatus
from app.models.round import Round
from app.schemas.betting import GoalIn
from app.services.settlement import settle_match


def _get_match(session: Session, match_id: uuid.UUID) -> Match:
    match = session.get(Match, match_id)
    if match is None:
        raise NotFound(f"match {match_id} not found")
    return match


def record_result(
    session: Session,
    match_id: uuid.UUID,
    home_score: int,
    away_score: int,
    goals: list[GoalIn],
    now: datetime,
) -> Match:
    match = _get_match(session, match_id)

    if len(goals) != home_score + away_score:
        raise InvalidSelection(
            "el numero de goles no cuadra con home_score + away_score"
        )

    valid_team_ids = {match.home_team_id, match.away_team_id}
    home_goals = 0
    away_goals = 0
    for goal in goals:
        if goal.team_id not in valid_team_ids:
            raise InvalidSelection(
                f"team {goal.team_id} does not play in match {match_id}"
            )
        if goal.team_id == match.home_team_id:
            home_goals += 1
        else:
            away_goals += 1

    if home_goals != home_score or away_goals != away_score:
        raise InvalidSelection(
            "el reparto de goles por equipo no cuadra con home_score/away_score"
        )

    for goal in goals:
        session.add(
            Goal(
                match_id=match.id,
                team_id=goal.team_id,
                minute=goal.minute,
                is_stoppage=goal.is_stoppage,
            )
        )

    match.home_score = home_score
    match.away_score = away_score
    match.status = MatchStatus.FINISHED
    session.flush()

    settle_match(session, match, now)
    return match


def get_round_results(
    session: Session, round_id: uuid.UUID
) -> list[tuple[Match, list[Goal]]]:
    round_ = session.get(Round, round_id)
    if round_ is None:
        raise NotFound(f"round {round_id} not found")

    matches = list(
        session.scalars(
            select(Match).where(Match.round_id == round_id).order_by(Match.kickoff_at)
        )
    )
    match_ids = [m.id for m in matches]
    goals_by_match: dict[uuid.UUID, list[Goal]] = {}
    if match_ids:
        for goal in session.scalars(select(Goal).where(Goal.match_id.in_(match_ids))):
            goals_by_match.setdefault(goal.match_id, []).append(goal)

    return [(match, goals_by_match.get(match.id, [])) for match in matches]
