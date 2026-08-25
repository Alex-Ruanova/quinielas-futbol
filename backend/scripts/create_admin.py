import argparse
import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User


def promote_to_admin(email: str) -> None:
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            print(f"No existe un usuario con email {email}", file=sys.stderr)
            raise SystemExit(1)
        user.is_admin = True
        session.commit()
        print(f"{email} promovido a administrador")


def main() -> None:
    parser = argparse.ArgumentParser(description="Promueve una cuenta a is_admin")
    parser.add_argument("email")
    args = parser.parse_args()
    promote_to_admin(args.email)


if __name__ == "__main__":
    main()
