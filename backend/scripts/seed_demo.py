"""Siembra una temporada navegable: equipos, jornadas y partidos en los cuatro
estados que muestra la tarjeta del diseño (abierto, por cerrar, cerrado, liquidado).

Idempotente: si la temporada ya existe, no hace nada.

Uso:
    DATABASE_URL=... uv run python scripts/seed_demo.py
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.engine.bands import GoalBand
from app.engine.config import SEED_CREDITS
from app.engine.selection import GoalBandSelection, OutcomeSelection
from app.models.credit_transaction import CreditTransactionKind
from app.models.match import Match, MatchStatus
from app.models.round import Round
from app.models.season import Season
from app.models.team import Team
from app.models.user import User
from app.schemas.betting import GoalIn
from app.services import betting as betting_service
from app.services import results as results_service
from app.services import wallet as wallet_service

SEASON_NAME = "Apertura 2026"
DEMO_PASSWORD = "quinielas2026"

# Jugadores de demo. Existen para que el ranking y el historial tengan contenido
# desde el primer minuto: un evaluador que entra no deberia ver tablas vacias.
DEMO_PLAYERS = [
    ("mariana@nexutest.mx", "Mariana R."),
    ("beto@nexutest.mx", "Beto Salas"),
    ("karla@nexutest.mx", "Karla Dominguez"),
]

# Fuerzas deliberadamente dispares: con 92 contra 24 la mecánica de momios
# (apostarle al grande paga poco) se ve sin tener que buscarla.
TEAMS: list[tuple[str, int]] = [
    ("Rayados", 92),
    ("America", 88),
    ("Tigres", 85),
    ("Cruz Azul", 79),
    ("Leon", 74),
    ("Chivas", 68),
    ("Santos", 61),
    ("Toluca", 57),
    ("Atlas", 52),
    ("Pumas", 46),
    ("Juarez", 44),
    ("Mazatlan", 38),
    ("Puebla", 31),
    ("Necaxa", 24),
]

# Los seis momios por franja del artboard C. Toda franja ausente cae al default
# del motor; se listan las seis para que el panel de admin tenga qué mostrar.
SCORING_CONFIG: dict[str, object] = {
    "outcome": 3,
    "exact_score": 5,
    "goal_band": 2,
    "goal_band_odds": {
        GoalBand.MIN_0_15.value: "4.60",
        GoalBand.MIN_16_30.value: "4.20",
        GoalBand.MIN_31_45.value: "3.80",
        GoalBand.MIN_46_60.value: "3.60",
        GoalBand.MIN_61_75.value: "3.90",
        GoalBand.MIN_76_90_PLUS.value: "3.30",
    },
}

# (local, visitante, offset respecto a "ahora")
CLOSING_SOON = [
    ("Cruz Azul", "Puebla", timedelta(minutes=9)),
    ("Chivas", "Mazatlan", timedelta(minutes=13)),
]
ALREADY_CLOSED = [
    ("Atlas", "Juarez", timedelta(minutes=-40)),
    ("Rayados", "Toluca", timedelta(hours=-30)),
    ("America", "Pumas", timedelta(hours=-52)),
]
OPEN_J14 = [
    ("Rayados", "Necaxa", timedelta(hours=5)),
    ("America", "Atlas", timedelta(hours=9)),
    ("Tigres", "Puebla", timedelta(hours=26)),
    ("Santos", "Toluca", timedelta(hours=50)),
]
OPEN_J15 = [
    ("Cruz Azul", "Chivas", timedelta(days=2, hours=3)),
    ("Leon", "Mazatlan", timedelta(days=2, hours=7)),
    ("Santos", "Juarez", timedelta(days=3, hours=2)),
    ("Necaxa", "Toluca", timedelta(days=3, hours=6)),
    ("Pumas", "Atlas", timedelta(days=4, hours=4)),
    ("Tigres", "America", timedelta(days=5, hours=1)),
]


def main() -> None:
    now = datetime.now(UTC)

    with SessionLocal() as session:
        if session.scalar(select(Season).where(Season.name == SEASON_NAME)):
            print(f"La temporada '{SEASON_NAME}' ya existe. Nada que hacer.")
            return

        teams: dict[str, Team] = {}
        for name, strength in TEAMS:
            team = session.scalar(select(Team).where(Team.name == name))
            if team is None:
                team = Team(name=name, strength=strength, crest_url=None)
                session.add(team)
            teams[name] = team
        session.flush()

        season = Season(
            name=SEASON_NAME,
            starts_on=date(2026, 8, 1),
            ends_on=date(2026, 12, 15),
            scoring_config=SCORING_CONFIG,
            status="active",
        )
        session.add(season)
        session.flush()

        j14 = Round(
            season_id=season.id,
            number=14,
            name="Jornada 14",
            opens_at=now - timedelta(days=4),
            closes_at=now + timedelta(days=4),
        )
        j15 = Round(
            season_id=season.id,
            number=15,
            name="Jornada 15",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(days=10),
        )
        session.add_all([j14, j15])
        session.flush()

        plan = (
            [(j14, h, a, off) for h, a, off in CLOSING_SOON]
            + [(j14, h, a, off) for h, a, off in ALREADY_CLOSED]
            + [(j14, h, a, off) for h, a, off in OPEN_J14]
            + [(j15, h, a, off) for h, a, off in OPEN_J15]
        )
        for round_, home, away, offset in plan:
            session.add(
                Match(
                    round_id=round_.id,
                    home_team_id=teams[home].id,
                    away_team_id=teams[away].id,
                    kickoff_at=now + offset,
                    status=MatchStatus.SCHEDULED,
                )
            )

        # Un partido ya jugado con apuestas liquidadas: sin esto, /ranking y
        # /mis-apuestas salen vacios y la demo no ensena lo que importa.
        played = Match(
            round_id=j14.id,
            home_team_id=teams["Leon"].id,
            away_team_id=teams["Necaxa"].id,
            kickoff_at=now - timedelta(hours=3),
            status=MatchStatus.SCHEDULED,
        )
        session.add(played)
        session.flush()

        players: list[User] = []
        for email, display_name in DEMO_PLAYERS:
            user = User(
                email=email,
                password_hash=hash_password(DEMO_PASSWORD),
                display_name=display_name,
                is_admin=False,
            )
            session.add(user)
            session.flush()
            wallet_service.post_transaction(
                session, user.id, CreditTransactionKind.SEED, SEED_CREDITS
            )
            players.append(user)
        session.flush()

        # El `now` es anterior al saque para que R3 permita apostar; el resultado
        # se captura justo despues.
        before_kickoff = played.kickoff_at - timedelta(hours=1)
        betting_service.upsert_prediction(
            session, players[0].id, played.id, 2, 1, before_kickoff
        )
        betting_service.upsert_prediction(
            session, players[1].id, played.id, 1, 1, before_kickoff
        )
        betting_service.upsert_prediction(
            session, players[2].id, played.id, 3, 0, before_kickoff
        )
        betting_service.place_bet(
            session,
            players[0].id,
            played.id,
            OutcomeSelection(market="OUTCOME", pick="HOME"),
            Decimal("100.00"),
            before_kickoff,
        )
        betting_service.place_bet(
            session,
            players[1].id,
            played.id,
            GoalBandSelection(
                market="GOAL_BAND", band=GoalBand.MIN_61_75, team_id=None
            ),
            Decimal("50.00"),
            before_kickoff,
        )
        betting_service.place_bet(
            session,
            players[2].id,
            played.id,
            OutcomeSelection(market="OUTCOME", pick="AWAY"),
            Decimal("80.00"),
            before_kickoff,
        )
        session.flush()

        results_service.record_result(
            session,
            played.id,
            home_score=2,
            away_score=1,
            goals=[
                GoalIn(team_id=teams["Leon"].id, minute=12),
                GoalIn(team_id=teams["Necaxa"].id, minute=55),
                GoalIn(team_id=teams["Leon"].id, minute=70),
            ],
            now=now,
        )

        session.commit()

        print(f"Temporada: {season.name}")
        print(f"Equipos:   {len(TEAMS)}  (de {TEAMS[-1][1]} a {TEAMS[0][1]} de fuerza)")
        print("Jornadas:  2")
        print(f"Partidos:  {len(plan)}")
        print(
            f"  abiertos={len(OPEN_J14) + len(OPEN_J15)} "
            f"por-cerrar={len(CLOSING_SOON)} cerrados={len(ALREADY_CLOSED)}"
        )
        print(f"Jugadores: {len(DEMO_PLAYERS)}  (password: {DEMO_PASSWORD})")
        for email, name in DEMO_PLAYERS:
            print(f"  {email:<24} {name}")
        print("Un partido liquidado (Leon 2-1 Necaxa) con apuestas y puntos.")


if __name__ == "__main__":
    main()
