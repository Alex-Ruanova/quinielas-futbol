"""Crea (o promueve) una cuenta de administrador de forma no interactiva.

A diferencia de `create_admin.py`, que exige que el usuario ya se haya registrado,
esta crea la cuenta si no existe. Sirve para arrancar un despliegue nuevo, donde
todavia no hay nadie.

Uso:
    ADMIN_EMAIL=a@b.com ADMIN_PASSWORD=... uv run python scripts/bootstrap_admin.py
"""

import os
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.engine.config import SEED_CREDITS
from app.models.credit_transaction import CreditTransactionKind
from app.models.user import User
from app.services.wallet import post_transaction


def main() -> None:
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        print("Faltan ADMIN_EMAIL y/o ADMIN_PASSWORD", file=sys.stderr)
        raise SystemExit(1)
    if len(password) < 8:
        print("ADMIN_PASSWORD debe tener al menos 8 caracteres", file=sys.stderr)
        raise SystemExit(1)

    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is not None:
            if user.is_admin:
                print(f"{email} ya es administrador. Nada que hacer.")
                return
            user.is_admin = True
            session.commit()
            print(f"{email} promovido a administrador")
            return

        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=os.getenv("ADMIN_DISPLAY_NAME", "Administrador"),
            is_admin=True,
        )
        session.add(user)
        session.flush()
        # Mismo saldo inicial que cualquier registro, por la misma puerta al ledger (R5).
        post_transaction(session, user.id, CreditTransactionKind.SEED, SEED_CREDITS)
        session.commit()
        print(f"{email} creado como administrador con {SEED_CREDITS} de saldo")


if __name__ == "__main__":
    main()
