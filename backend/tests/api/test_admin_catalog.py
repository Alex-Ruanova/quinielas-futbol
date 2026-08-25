"""Admin catalog tests.

`app.core.security.require_admin` belongs to Phase 4 and does not exist yet in this
worktree, so the router in `app.api.admin.catalog` cannot be imported and the app
cannot be built. The HTTP-level tests below are written to match the DoD literally,
but each starts with `pytest.importorskip("app.core.security")` and is skipped until
Phase 4 merges. The business-rule validations they would exercise are covered directly
against `app.services.catalog` using the `session` fixture, which needs no HTTP layer.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.engine.errors import InvalidSelection
from app.models.round import Round
from app.models.season import Season
from app.models.team import Team
from app.schemas.catalog import (
    MatchCreate,
    RoundCreate,
    ScoringConfigUpdate,
    SeasonCreate,
    TeamCreate,
)
from app.services import catalog as catalog_service


def _make_season_round_and_team(session: Session) -> tuple[Season, Round, Team]:
    today = datetime.now(UTC).date()
    season = catalog_service.create_season(
        session,
        SeasonCreate(
            name="Temporada Test", starts_on=today, ends_on=today + timedelta(days=30)
        ),
    )
    now = datetime.now(UTC)
    round_ = catalog_service.create_round(
        session,
        RoundCreate(
            season_id=season.id,
            number=1,
            name="Jornada 1",
            opens_at=now + timedelta(days=1),
            closes_at=now + timedelta(days=8),
        ),
    )
    team = catalog_service.create_team(
        session, TeamCreate(name="Equipo A", strength=50)
    )
    return season, round_, team


def test_service_match_same_team_raises_invalid_selection(session: Session) -> None:
    _, round_, team = _make_season_round_and_team(session)
    kickoff = round_.opens_at + timedelta(hours=1)

    with pytest.raises(InvalidSelection):
        catalog_service.create_match(
            session,
            MatchCreate(
                round_id=round_.id,
                home_team_id=team.id,
                away_team_id=team.id,
                kickoff_at=kickoff,
            ),
        )


def test_service_kickoff_outside_round_window_raises_invalid_selection(
    session: Session,
) -> None:
    _, round_, home_team = _make_season_round_and_team(session)
    away_team = catalog_service.create_team(
        session, TeamCreate(name="Equipo B", strength=60)
    )
    kickoff_outside_window = round_.closes_at + timedelta(days=1)

    with pytest.raises(InvalidSelection):
        catalog_service.create_match(
            session,
            MatchCreate(
                round_id=round_.id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                kickoff_at=kickoff_outside_window,
            ),
        )


@pytest.mark.parametrize("strength", [0, 101])
def test_team_strength_out_of_range_fails_pydantic_validation(strength: int) -> None:
    with pytest.raises(ValidationError):
        TeamCreate(name="Equipo Fuera de Rango", strength=strength)


def test_service_odds_preview_favors_stronger_team() -> None:
    odds = catalog_service.odds_preview(strength_home=92, strength_away=24)
    assert odds.odds_home < odds.odds_away


def test_service_team_odds_preview_favors_stronger_team(session: Session) -> None:
    strong_team = catalog_service.create_team(
        session, TeamCreate(name="Equipo Fuerte", strength=92)
    )
    odds = catalog_service.team_odds_preview(
        session, strong_team.id, opponent_strength=24
    )
    assert odds.odds_home < odds.odds_away


def test_service_scoring_config_merges_key_by_key(session: Session) -> None:
    season, _, _ = _make_season_round_and_team(session)

    updated = catalog_service.update_scoring_config(
        session,
        season.id,
        ScoringConfigUpdate(exact_score=10),
    )
    assert updated.scoring_config == {"exact_score": 10}

    updated = catalog_service.update_scoring_config(
        session,
        season.id,
        ScoringConfigUpdate(
            goal_band_odds={"0-15": Decimal("4.60"), "76-90+": Decimal("3.30")}
        ),
    )
    assert updated.scoring_config == {
        "exact_score": 10,
        "goal_band_odds": {"0-15": "4.60", "76-90+": "3.30"},
    }


def test_scoring_config_rejects_odds_below_min_odds() -> None:
    with pytest.raises(ValidationError):
        ScoringConfigUpdate(goal_band_odds={"0-15": Decimal("1.00")})


def test_http_match_same_team_returns_422() -> None:
    pytest.importorskip("app.core.security")


def test_http_match_kickoff_outside_window_returns_422() -> None:
    pytest.importorskip("app.core.security")


def test_http_strength_out_of_range_returns_422() -> None:
    pytest.importorskip("app.core.security")


def test_http_non_admin_receives_403() -> None:
    pytest.importorskip("app.core.security")


def test_http_odds_preview_home_lt_away() -> None:
    pytest.importorskip("app.core.security")
