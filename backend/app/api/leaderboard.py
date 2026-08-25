from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_current_user
from app.db.session import get_session
from app.schemas.betting import LeaderboardEntryRead
from app.services import leaderboard as leaderboard_service

router = APIRouter(prefix="/api/v1/seasons", tags=["leaderboard"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/{season_id}/leaderboard", response_model=list[LeaderboardEntryRead])
def get_leaderboard(
    season_id: UUID,
    session: SessionDep,
    _: Annotated[object, Depends(require_current_user)],
) -> list[LeaderboardEntryRead]:
    rows = leaderboard_service.get_leaderboard(session, season_id)
    return [
        LeaderboardEntryRead(
            user_id=row.user_id,
            display_name=row.display_name,
            points=row.points,
            exact_scores=row.exact_scores,
            balance=row.balance,
        )
        for row in rows
    ]
