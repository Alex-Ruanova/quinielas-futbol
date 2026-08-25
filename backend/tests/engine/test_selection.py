import pytest
from pydantic import ValidationError

from app.engine.selection import GoalBandSelection, OutcomeSelection


def test_invalid_goal_band_is_rejected() -> None:
    with pytest.raises(ValidationError):
        GoalBandSelection(band="20-40")


def test_valid_goal_band_selection() -> None:
    selection = GoalBandSelection(band="0-15")
    assert selection.team_id is None


def test_outcome_selection_requires_valid_pick() -> None:
    with pytest.raises(ValidationError):
        OutcomeSelection(pick="TIE")
