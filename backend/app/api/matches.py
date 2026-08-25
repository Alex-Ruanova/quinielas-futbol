from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import require_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.betting import (
    BetCreate,
    BetRead,
    GoalRead,
    MatchResultRead,
    MatchUpcomingRead,
    PredictionIn,
    PredictionRead,
)
from app.services import betting as betting_service
from app.services import results as results_service

router = APIRouter(prefix="/api/v1", tags=["matches"])

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(require_current_user)]


@router.get("/matches/upcoming", response_model=list[MatchUpcomingRead])
def list_upcoming_matches(
    user: CurrentUser, session: SessionDep
) -> list[MatchUpcomingRead]:
    now = datetime.now(UTC)
    data = betting_service.list_upcoming_matches(session, user.id, now)
    return [MatchUpcomingRead.model_validate(item) for item in data]


@router.put("/matches/{match_id}/prediction", response_model=PredictionRead)
def upsert_prediction(
    match_id: UUID, data: PredictionIn, user: CurrentUser, session: SessionDep
) -> PredictionRead:
    now = datetime.now(UTC)
    prediction = betting_service.upsert_prediction(
        session,
        user.id,
        match_id,
        data.predicted_home_score,
        data.predicted_away_score,
        now,
    )
    session.commit()
    return PredictionRead.model_validate(prediction)


@router.post(
    "/matches/{match_id}/bets",
    response_model=BetRead,
    status_code=status.HTTP_201_CREATED,
)
def place_bet(
    match_id: UUID, data: BetCreate, user: CurrentUser, session: SessionDep
) -> BetRead:
    now = datetime.now(UTC)
    bet = betting_service.place_bet(
        session, user.id, match_id, data.selection, data.stake, now
    )
    session.commit()
    return BetRead.model_validate(bet)


@router.get("/rounds/{round_id}/results", response_model=list[MatchResultRead])
def get_round_results(round_id: UUID, session: SessionDep) -> list[MatchResultRead]:
    rows = results_service.get_round_results(session, round_id)
    return [
        MatchResultRead(
            id=match.id,
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            status=match.status,
            home_score=match.home_score,
            away_score=match.away_score,
            goals=[GoalRead.model_validate(goal) for goal in goals],
        )
        for match, goals in rows
    ]
