from datetime import UTC, date, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Goal, Match, MatchStatus, Prediction, Round, Season, Team, User


def _make_season(session: Session) -> Season:
    season = Season(name="Liga MX 2026", starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 1))
    session.add(season)
    session.flush()
    return season


def _make_round(session: Session, season: Season) -> Round:
    round_ = Round(
        season_id=season.id,
        number=1,
        name="Jornada 1",
        opens_at=datetime(2026, 1, 1, tzinfo=UTC),
        closes_at=datetime(2026, 1, 8, tzinfo=UTC),
    )
    session.add(round_)
    session.flush()
    return round_


def _make_team(session: Session, name: str, strength: int) -> Team:
    team = Team(name=name, strength=strength)
    session.add(team)
    session.flush()
    return team


@pytest.mark.parametrize("strength", [0, 101])
def test_team_strength_check_constraint_rejects_out_of_range(session: Session, strength: int) -> None:
    team = Team(name="Equipo Invalido", strength=strength)
    session.add(team)
    with pytest.raises(IntegrityError):
        session.flush()


def test_prediction_duplicate_user_match_violates_unique_constraint(session: Session) -> None:
    season = _make_season(session)
    round_ = _make_round(session, season)
    home = _make_team(session, "Local", 80)
    away = _make_team(session, "Visitante", 40)
    match = Match(
        round_id=round_.id,
        home_team_id=home.id,
        away_team_id=away.id,
        kickoff_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    session.add(match)
    user = User(email="alex@example.com", password_hash="hash", display_name="Alex")
    session.add(user)
    session.flush()

    session.add(Prediction(user_id=user.id, match_id=match.id, predicted_home_score=1, predicted_away_score=0))
    session.flush()

    session.add(Prediction(user_id=user.id, match_id=match.id, predicted_home_score=2, predicted_away_score=1))
    with pytest.raises(IntegrityError):
        session.flush()


def test_match_with_teams_and_goals_persists_and_rereads_with_correct_types(session: Session) -> None:
    season = _make_season(session)
    round_ = _make_round(session, season)
    home = _make_team(session, "Local", 90)
    away = _make_team(session, "Visitante", 30)
    kickoff = datetime(2026, 3, 1, 15, 0, tzinfo=UTC)
    match = Match(
        round_id=round_.id,
        home_team_id=home.id,
        away_team_id=away.id,
        kickoff_at=kickoff,
        status=MatchStatus.FINISHED,
        home_score=2,
        away_score=1,
    )
    session.add(match)
    session.flush()

    goal = Goal(match_id=match.id, team_id=home.id, minute=90, is_stoppage=True)
    session.add(goal)
    session.flush()
    session.expire_all()

    persisted = session.get(Match, match.id)
    assert persisted is not None
    assert persisted.status is MatchStatus.FINISHED
    assert persisted.kickoff_at.tzinfo is not None
    assert isinstance(persisted.home_score, int)

    persisted_goal = session.get(Goal, goal.id)
    assert persisted_goal is not None
    assert persisted_goal.is_stoppage is True
    assert persisted_goal.minute == 90
