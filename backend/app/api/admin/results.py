from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_session
from app.engine.errors import NotFound
from app.models.match import Match
from app.schemas.betting import GoalRead, MatchResultRead, ResultIn
from app.services import results as results_service
from app.services import settlement as settlement_service

router = APIRouter(
    prefix="/api/v1/admin/matches",
    dependencies=[Depends(require_admin)],
    tags=["admin-results"],
)

SessionDep = Annotated[Session, Depends(get_session)]


def _get_match(session: Session, match_id: UUID) -> Match:
    match = session.get(Match, match_id)
    if match is None:
        raise NotFound(f"match {match_id} not found")
    return match


@router.put("/{match_id}/result", response_model=MatchResultRead)
def record_result(
    match_id: UUID, data: ResultIn, session: SessionDep
) -> MatchResultRead:
    now = datetime.now(UTC)
    match = results_service.record_result(
        session, match_id, data.home_score, data.away_score, data.goals, now
    )
    session.commit()
    return MatchResultRead(
        id=match.id,
        home_team_id=match.home_team_id,
        away_team_id=match.away_team_id,
        status=match.status,
        home_score=match.home_score,
        away_score=match.away_score,
        goals=[
            GoalRead(team_id=g.team_id, minute=g.minute, is_stoppage=g.is_stoppage)
            for g in data.goals
        ],
    )


@router.post("/{match_id}/settle", status_code=status.HTTP_204_NO_CONTENT)
def settle_match(match_id: UUID, session: SessionDep) -> None:
    match = _get_match(session, match_id)
    settlement_service.settle_match(session, match, datetime.now(UTC))
    session.commit()


@router.post("/{match_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_match(match_id: UUID, session: SessionDep) -> None:
    match = _get_match(session, match_id)
    settlement_service.cancel_match(session, match, datetime.now(UTC))
    session.commit()
