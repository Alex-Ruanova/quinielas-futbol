"""Seed a navigable demo season: teams, two rounds, matches in the future.

Idempotent: re-running it after a successful seed is a no-op.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.season import Season
from app.models.team import Team
from app.schemas.catalog import MatchCreate, RoundCreate, SeasonCreate, TeamCreate
from app.services import catalog as catalog_service

SEASON_NAME = "Temporada Demo"

TEAM_STRENGTHS = [
    ("Tigres del Norte", 92),
    ("Águilas Doradas", 78),
    ("Leones FC", 65),
    ("Halcones Azules", 58),
    ("Panteras Rojas", 47),
    ("Cóndores", 40),
    ("Lobos del Sur", 33),
    ("Escorpiones", 24),
]


def main() -> None:
    session = SessionLocal()
    try:
        existing = session.scalar(select(Season).where(Season.name == SEASON_NAME))
        if existing is not None:
            print(
                f"Ya existe la temporada '{SEASON_NAME}' (id={existing.id}). "
                "Nada que hacer."
            )
            return

        teams: list[Team] = [
            catalog_service.create_team(
                session, TeamCreate(name=name, strength=strength)
            )
            for name, strength in TEAM_STRENGTHS
        ]

        today = datetime.now(UTC).date()
        season = catalog_service.create_season(
            session,
            SeasonCreate(
                name=SEASON_NAME,
                starts_on=today,
                ends_on=today + timedelta(days=60),
            ),
        )

        now = datetime.now(UTC)
        round_specs = [
            (1, "Jornada 1", now + timedelta(days=1), now + timedelta(days=8)),
            (2, "Jornada 2", now + timedelta(days=8), now + timedelta(days=15)),
        ]
        pairings = [
            (0, 7),  # strength 92 vs 24 -> clearly lopsided odds
            (1, 6),
            (2, 5),
            (3, 4),
        ]

        for number, name, opens_at, closes_at in round_specs:
            round_ = catalog_service.create_round(
                session,
                RoundCreate(
                    season_id=season.id,
                    number=number,
                    name=name,
                    opens_at=opens_at,
                    closes_at=closes_at,
                ),
            )
            kickoff_at = opens_at + timedelta(hours=2)
            for home_idx, away_idx in pairings:
                catalog_service.create_match(
                    session,
                    MatchCreate(
                        round_id=round_.id,
                        home_team_id=teams[home_idx].id,
                        away_team_id=teams[away_idx].id,
                        kickoff_at=kickoff_at,
                    ),
                )

        session.commit()
        print(
            f"Temporada '{SEASON_NAME}' creada (id={season.id}) con "
            f"{len(teams)} equipos y {len(round_specs)} jornadas."
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
