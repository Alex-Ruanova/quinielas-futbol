import pytest

from app.engine.errors import InvalidSelection
from app.engine.scoring import Score, ScoringRules, score_prediction


def test_exact_score_awards_default_eight_points() -> None:
    rules = ScoringRules.from_config(None)
    predicted = Score(home=2, away=1)
    actual = Score(home=2, away=1)
    assert score_prediction(predicted, actual, rules) == 8


def test_right_winner_wrong_score_awards_three_points() -> None:
    rules = ScoringRules.from_config(None)
    predicted = Score(home=3, away=1)
    actual = Score(home=2, away=0)
    assert score_prediction(predicted, actual, rules) == 3


def test_wrong_winner_awards_zero_points() -> None:
    rules = ScoringRules.from_config(None)
    predicted = Score(home=1, away=0)
    actual = Score(home=0, away=1)
    assert score_prediction(predicted, actual, rules) == 0


def test_from_config_merges_key_by_key() -> None:
    rules = ScoringRules.from_config({"exact_score": 10})
    predicted = Score(home=2, away=2)
    actual = Score(home=2, away=2)
    assert score_prediction(predicted, actual, rules) == 13

    predicted_winner_only = Score(home=5, away=1)
    actual_other_score = Score(home=1, away=0)
    assert score_prediction(predicted_winner_only, actual_other_score, rules) == 3


@pytest.mark.parametrize("raw", [{"outcome": "abc"}, {"outcome": -3}])
def test_from_config_rejects_corrupt_jsonb_as_domain_error(
    raw: dict[str, object],
) -> None:
    with pytest.raises(InvalidSelection):
        ScoringRules.from_config(raw)
