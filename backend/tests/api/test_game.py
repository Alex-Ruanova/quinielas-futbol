import uuid
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.engine.config import DEFAULT_GOAL_BAND_ODDS
from app.models.bet import Bet
from app.models.match import Match
from app.models.team import Team
from app.models.user import User
from app.schemas.catalog import (
    MatchCreate,
    RoundCreate,
    SeasonCreate,
    TeamCreate,
    TeamUpdate,
)
from app.services import catalog as catalog_service
from app.services import users as users_service
from app.services import wallet

CENTS = Decimal("0.01")


def _register(
    session: Session, email: str, *, admin: bool = False
) -> tuple[User, dict[str, str]]:
    user = users_service.register(
        session, email=email, password="testpass123", display_name=email
    )
    if admin:
        user.is_admin = True
        session.commit()
    token = create_access_token(user.id)
    return user, {"Authorization": f"Bearer {token}"}


def _setup_match(
    session: Session,
    kickoff_at: datetime,
    opens_at: datetime | None = None,
    closes_at: datetime | None = None,
) -> tuple[Team, Team, Match]:
    opens_at = opens_at or kickoff_at - timedelta(days=1)
    closes_at = closes_at or kickoff_at + timedelta(days=1)
    season = catalog_service.create_season(
        session,
        SeasonCreate(
            name="Temporada HTTP",
            starts_on=kickoff_at.date(),
            ends_on=(kickoff_at + timedelta(days=90)).date(),
        ),
    )
    round_ = catalog_service.create_round(
        session,
        RoundCreate(
            season_id=season.id,
            number=1,
            name="Jornada 1",
            opens_at=opens_at,
            closes_at=closes_at,
        ),
    )
    home = catalog_service.create_team(session, TeamCreate(name="Local", strength=70))
    away = catalog_service.create_team(
        session, TeamCreate(name="Visitante", strength=40)
    )
    match = catalog_service.create_match(
        session,
        MatchCreate(
            round_id=round_.id,
            home_team_id=home.id,
            away_team_id=away.id,
            kickoff_at=kickoff_at,
        ),
    )
    session.commit()
    return home, away, match


async def test_place_bet_debits_stake_and_creates_pending_bet(
    client: AsyncClient, session: Session
) -> None:
    _, _, match = _setup_match(session, datetime.now(UTC) + timedelta(days=1))
    _, headers = _register(session, "bettor1@example.com")

    response = await client.post(
        f"/api/v1/matches/{match.id}/bets",
        json={"selection": {"market": "OUTCOME", "pick": "HOME"}, "stake": "100"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["odds_snapshot"] is not None

    wallet_response = await client.get("/api/v1/wallet", headers=headers)
    assert wallet_response.json()["balance"] == "900.00"


async def test_place_bet_after_kickoff_closed_returns_409_and_balance_unchanged(
    client: AsyncClient, session: Session
) -> None:
    past_kickoff = datetime.now(UTC) - timedelta(hours=2)
    _, _, match = _setup_match(session, past_kickoff)
    _, headers = _register(session, "late-bettor@example.com")

    response = await client.post(
        f"/api/v1/matches/{match.id}/bets",
        json={"selection": {"market": "OUTCOME", "pick": "HOME"}, "stake": "50"},
        headers=headers,
    )
    assert response.status_code == 409

    balance = await client.get("/api/v1/wallet", headers=headers)
    assert balance.json()["balance"] == "1000.00"


async def test_stake_out_of_range_and_insufficient_balance(
    client: AsyncClient, session: Session
) -> None:
    _, _, match = _setup_match(session, datetime.now(UTC) + timedelta(days=1))
    user, headers = _register(session, "stakes@example.com")

    too_low = await client.post(
        f"/api/v1/matches/{match.id}/bets",
        json={"selection": {"market": "OUTCOME", "pick": "HOME"}, "stake": "5"},
        headers=headers,
    )
    assert too_low.status_code == 422

    too_high = await client.post(
        f"/api/v1/matches/{match.id}/bets",
        json={"selection": {"market": "OUTCOME", "pick": "HOME"}, "stake": "501"},
        headers=headers,
    )
    assert too_high.status_code == 422

    wallet.debit(session, user.id, Decimal("995.00"))
    session.commit()

    insufficient = await client.post(
        f"/api/v1/matches/{match.id}/bets",
        json={"selection": {"market": "OUTCOME", "pick": "HOME"}, "stake": "10"},
        headers=headers,
    )
    assert insufficient.status_code == 402

    bets = session.scalars(select(Bet).where(Bet.user_id == user.id)).all()
    assert bets == []


async def test_odds_snapshot_frozen_after_team_strength_change(
    client: AsyncClient, session: Session
) -> None:
    home, _, match = _setup_match(session, datetime.now(UTC) + timedelta(days=1))
    _, headers = _register(session, "r4@example.com")

    response = await client.post(
        f"/api/v1/matches/{match.id}/bets",
        json={"selection": {"market": "OUTCOME", "pick": "HOME"}, "stake": "50"},
        headers=headers,
    )
    assert response.status_code == 201
    bet_id = uuid.UUID(response.json()["id"])
    original_odds = response.json()["odds_snapshot"]

    catalog_service.update_team(session, home.id, TeamUpdate(strength=5))
    session.commit()

    bet_row = session.get(Bet, bet_id)
    assert bet_row is not None
    assert str(bet_row.odds_snapshot) == original_odds


async def test_goal_band_bet_with_non_participant_team_returns_422(
    client: AsyncClient, session: Session
) -> None:
    _, _, match = _setup_match(session, datetime.now(UTC) + timedelta(days=1))
    outsider = catalog_service.create_team(
        session, TeamCreate(name="Fuera", strength=50)
    )
    session.commit()
    _, headers = _register(session, "goalband@example.com")

    response = await client.post(
        f"/api/v1/matches/{match.id}/bets",
        json={
            "selection": {
                "market": "GOAL_BAND",
                "band": "0-15",
                "team_id": str(outsider.id),
            },
            "stake": "20",
        },
        headers=headers,
    )
    assert response.status_code == 422

    balance = await client.get("/api/v1/wallet", headers=headers)
    assert balance.json()["balance"] == "1000.00"


async def test_e2e_match_result_settles_bets_with_exact_payout(
    client: AsyncClient, session: Session
) -> None:
    kickoff = datetime.now(UTC) + timedelta(days=1)
    home, away, match = _setup_match(session, kickoff)
    _, admin_headers = _register(session, "admin-e2e@example.com", admin=True)
    _, home_headers = _register(session, "home-bettor@example.com")
    _, band_headers = _register(session, "band-bettor@example.com")

    home_stake = Decimal(100)
    band_stake = Decimal(60)

    home_bet_resp = await client.post(
        f"/api/v1/matches/{match.id}/bets",
        json={
            "selection": {"market": "OUTCOME", "pick": "HOME"},
            "stake": str(home_stake),
        },
        headers=home_headers,
    )
    assert home_bet_resp.status_code == 201
    home_odds = Decimal(home_bet_resp.json()["odds_snapshot"])

    band_bet_resp = await client.post(
        f"/api/v1/matches/{match.id}/bets",
        json={
            "selection": {"market": "GOAL_BAND", "band": "61-75"},
            "stake": str(band_stake),
        },
        headers=band_headers,
    )
    assert band_bet_resp.status_code == 201
    band_odds = Decimal(band_bet_resp.json()["odds_snapshot"])
    assert band_odds == DEFAULT_GOAL_BAND_ODDS

    result_resp = await client.put(
        f"/api/v1/admin/matches/{match.id}/result",
        json={
            "home_score": 2,
            "away_score": 1,
            "goals": [
                {"team_id": str(home.id), "minute": 12, "is_stoppage": False},
                {"team_id": str(home.id), "minute": 70, "is_stoppage": False},
                {"team_id": str(away.id), "minute": 55, "is_stoppage": False},
            ],
        },
        headers=admin_headers,
    )
    assert result_resp.status_code == 200

    home_balance = await client.get("/api/v1/wallet", headers=home_headers)
    band_balance = await client.get("/api/v1/wallet", headers=band_headers)

    home_payout = (home_stake * home_odds).quantize(CENTS, rounding=ROUND_HALF_UP)
    band_payout = (band_stake * band_odds).quantize(CENTS, rounding=ROUND_HALF_UP)

    expected_home_balance = (Decimal("1000.00") - home_stake + home_payout).quantize(
        CENTS
    )
    expected_band_balance = (Decimal("1000.00") - band_stake + band_payout).quantize(
        CENTS
    )

    assert Decimal(home_balance.json()["balance"]) == expected_home_balance
    assert Decimal(band_balance.json()["balance"]) == expected_band_balance
