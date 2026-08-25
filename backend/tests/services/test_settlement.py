from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.engine.selection import OutcomeSelection
from app.models.bet import Bet, BetStatus
from app.models.credit_transaction import CreditTransaction
from app.models.match import Match, MatchStatus
from app.models.prediction import Prediction
from app.models.round import Round
from app.models.season import Season
from app.models.team import Team
from app.models.user import User
from app.schemas.catalog import MatchCreate, RoundCreate, SeasonCreate, TeamCreate
from app.services import betting, settlement, wallet
from app.services import catalog as catalog_service
from app.services import users as users_service


def _setup_match(
    session: Session, kickoff_at: datetime
) -> tuple[Season, Round, Team, Team, Match]:
    opens_at = kickoff_at - timedelta(days=1)
    closes_at = kickoff_at + timedelta(days=1)
    season = catalog_service.create_season(
        session,
        SeasonCreate(
            name="Temporada Liquidacion",
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
    home = catalog_service.create_team(session, TeamCreate(name="Local", strength=80))
    away = catalog_service.create_team(
        session, TeamCreate(name="Visitante", strength=20)
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
    session.flush()
    return season, round_, home, away, match


def _register(session: Session, email: str) -> User:
    return users_service.register(
        session, email=email, password="testpass123", display_name=email
    )


def test_settle_match_is_idempotent_across_three_calls(session: Session) -> None:
    kickoff = datetime.now(UTC) + timedelta(hours=2)
    _, _, _home, _away, match = _setup_match(session, kickoff)
    user = _register(session, "r6@example.com")

    bet = betting.place_bet(
        session,
        user.id,
        match.id,
        OutcomeSelection(pick="HOME"),
        Decimal(100),
        datetime.now(UTC),
    )
    session.flush()

    match.home_score = 2
    match.away_score = 0
    match.status = MatchStatus.FINISHED
    session.flush()

    settlement.settle_match(session, match, datetime.now(UTC))
    balance_after_first = wallet.get_balance(session, user.id)
    tx_count_after_first = session.scalar(
        select(func.count())
        .select_from(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
    )

    settlement.settle_match(session, match, datetime.now(UTC))
    settlement.settle_match(session, match, datetime.now(UTC))

    balance_after_third = wallet.get_balance(session, user.id)
    tx_count_after_third = session.scalar(
        select(func.count())
        .select_from(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
    )

    assert balance_after_first == balance_after_third
    assert tx_count_after_first == tx_count_after_third

    refreshed_bet = session.get(Bet, bet.id)
    assert refreshed_bet is not None
    assert refreshed_bet.status == BetStatus.WON


def test_cancel_match_voids_bets_refunds_stake_and_awards_no_points(
    session: Session,
) -> None:
    kickoff = datetime.now(UTC) + timedelta(hours=2)
    _, _, _home, _away, match = _setup_match(session, kickoff)
    user1 = _register(session, "r9-a@example.com")
    user2 = _register(session, "r9-b@example.com")

    bet1 = betting.place_bet(
        session,
        user1.id,
        match.id,
        OutcomeSelection(pick="HOME"),
        Decimal(100),
        datetime.now(UTC),
    )
    bet2 = betting.place_bet(
        session,
        user2.id,
        match.id,
        OutcomeSelection(pick="AWAY"),
        Decimal(50),
        datetime.now(UTC),
    )
    session.flush()

    settlement.cancel_match(session, match, datetime.now(UTC))

    refreshed_bet1 = session.get(Bet, bet1.id)
    refreshed_bet2 = session.get(Bet, bet2.id)
    assert refreshed_bet1 is not None
    assert refreshed_bet2 is not None
    assert refreshed_bet1.status == BetStatus.VOID
    assert refreshed_bet2.status == BetStatus.VOID

    assert wallet.get_balance(session, user1.id) == Decimal("1000.00")
    assert wallet.get_balance(session, user2.id) == Decimal("1000.00")

    predictions = session.scalars(
        select(Prediction).where(Prediction.match_id == match.id)
    ).all()
    assert all(p.points_awarded is None for p in predictions)


def test_predictor_without_bet_receives_points_with_balance_intact(
    session: Session,
) -> None:
    kickoff = datetime.now(UTC) + timedelta(hours=2)
    _, _, _home, _away, match = _setup_match(session, kickoff)
    user = _register(session, "r7@example.com")

    prediction = betting.upsert_prediction(
        session, user.id, match.id, 2, 0, datetime.now(UTC)
    )
    session.flush()

    match.home_score = 2
    match.away_score = 0
    match.status = MatchStatus.FINISHED
    session.flush()

    settlement.settle_match(session, match, datetime.now(UTC))

    refreshed = session.get(Prediction, prediction.id)
    assert refreshed is not None
    assert refreshed.points_awarded == 3 + 5

    assert wallet.get_balance(session, user.id) == Decimal("1000.00")
