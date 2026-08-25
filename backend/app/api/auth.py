from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_session
from app.schemas.user import TokenOut, UserLogin, UserOut, UserRegister
from app.services.users import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    authenticate,
    register,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegister, session: Annotated[Session, Depends(get_session)]
) -> UserOut:
    try:
        user = register(
            session,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            phone=payload.phone,
            contact_email=payload.contact_email,
        )
    except EmailAlreadyRegistered as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenOut)
def login(
    payload: UserLogin, session: Annotated[Session, Depends(get_session)]
) -> TokenOut:
    try:
        user = authenticate(session, email=payload.email, password=payload.password)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    return TokenOut(access_token=create_access_token(user.id))
