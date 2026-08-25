from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from app.services.users import update_profile

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(user: Annotated[User, Depends(require_current_user)]) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
def patch_me(
    payload: UserUpdate,
    user: Annotated[User, Depends(require_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> UserOut:
    updated = update_profile(
        session,
        user.id,
        display_name=payload.display_name,
        phone=payload.phone,
        contact_email=payload.contact_email,
    )
    return UserOut.model_validate(updated)
