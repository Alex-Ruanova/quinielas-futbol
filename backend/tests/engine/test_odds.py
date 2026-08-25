from decimal import Decimal

from app.engine.config import MIN_ODDS
from app.engine.odds import MatchOdds, OddsConfig, compute_odds


def test_favorite_home_has_lower_odds_full_sweep() -> None:
    config = OddsConfig()
    for strength_home in range(1, 101):
        for strength_away in range(1, 101):
            odds = compute_odds(strength_home, strength_away, config)
            if strength_home > strength_away:
                assert odds.odds_home < odds.odds_away, (strength_home, strength_away, odds)


def test_house_margin_positive_full_sweep() -> None:
    config = OddsConfig()
    for strength_home in range(1, 101):
        for strength_away in range(1, 101):
            odds = compute_odds(strength_home, strength_away, config)
            implied = (
                Decimal(1) / odds.odds_home
                + Decimal(1) / odds.odds_draw
                + Decimal(1) / odds.odds_away
            )
            assert implied > Decimal("1.0"), (strength_home, strength_away, odds, implied)


def test_no_odds_below_minimum_full_sweep() -> None:
    config = OddsConfig()
    for strength_home in range(1, 101):
        for strength_away in range(1, 101):
            odds = compute_odds(strength_home, strength_away, config)
            assert odds.odds_home >= MIN_ODDS
            assert odds.odds_draw >= MIN_ODDS
            assert odds.odds_away >= MIN_ODDS


def test_compute_odds_is_deterministic() -> None:
    config = OddsConfig()
    first = compute_odds(70, 40, config)
    second = compute_odds(70, 40, config)
    assert first == second
    assert isinstance(first, MatchOdds)
