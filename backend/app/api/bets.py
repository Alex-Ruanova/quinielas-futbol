from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_current_user
from app.db.session import get_session
from app.models.bet import BetStatus
from app.models.user import User
from app.schemas.betting import BetMatchRead, BetWithMatchRead
from app.services import betting as betting_service

router = APIRouter(prefix="/api/v1/bets", tags=["bets"])

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(require_current_user)]


@router.get("", response_model=list[BetWithMatchRead])
def list_my_bets(
    user: CurrentUser, session: SessionDep, status: BetStatus | None = None
) -> list[BetWithMatchRead]:
    rows = betting_service.list_bets_with_match(session, user.id, status)
    return [
        BetWithMatchRead(
            id=bet.id,
            match_id=bet.match_id,
            market=bet.market,
            selection=bet.selection,
            stake=bet.stake,
            odds_snapshot=bet.odds_snapshot,
            status=bet.status,
            settled_at=bet.settled_at,
            created_at=bet.created_at,
            match=BetMatchRead(
                home_team_name=home_name,
                away_team_name=away_name,
                kickoff_at=match.kickoff_at,
                status=match.status,
                home_score=match.home_score,
                away_score=match.away_score,
            ),
        )
        for bet, match, home_name, away_name in rows
    ]
