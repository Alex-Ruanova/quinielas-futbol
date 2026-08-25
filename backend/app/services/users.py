import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.engine.config import SEED_CREDITS
from app.engine.errors import NotFound
from app.models.credit_transaction import CreditTransactionKind
from app.models.user import User
from app.services.wallet import post_transaction


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass


def register(
    session: Session,
    email: str,
    password: str,
    display_name: str,
    phone: str | None = None,
    contact_email: str | None = None,
) -> User:
    existing = session.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise EmailAlreadyRegistered(f"El email {email} ya esta registrado")

    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
        phone=phone,
        contact_email=contact_email,
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise EmailAlreadyRegistered(f"El email {email} ya esta registrado") from exc

    post_transaction(session, user.id, CreditTransactionKind.SEED, SEED_CREDITS)
    session.commit()
    return user


def authenticate(session: Session, email: str, password: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentials("Email o contrasena incorrectos")
    return user


def update_profile(
    session: Session,
    user_id: uuid.UUID,
    display_name: str | None = None,
    phone: str | None = None,
    contact_email: str | None = None,
) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise NotFound("Usuario no encontrado")

    if display_name is not None:
        user.display_name = display_name
    if phone is not None:
        user.phone = phone
    if contact_email is not None:
        user.contact_email = contact_email

    session.commit()
    return user
