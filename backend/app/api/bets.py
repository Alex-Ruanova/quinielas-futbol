from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_current_user
from app.db.session import get_session
from app.models.bet import BetStatus
from app.models.user import User
from app.schemas.betting import BetRead
from app.services import betting as betting_service

router = APIRouter(prefix="/api/v1/bets", tags=["bets"])

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(require_current_user)]


@router.get("", response_model=list[BetRead])
def list_my_bets(
    user: CurrentUser, session: SessionDep, status: BetStatus | None = None
) -> list[BetRead]:
    bets = betting_service.list_bets(session, user.id, status)
    return [BetRead.model_validate(bet) for bet in bets]
