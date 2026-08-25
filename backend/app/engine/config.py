from decimal import Decimal

HOME_ADVANTAGE = 0.10
DRAW_BASE = 0.28
MARGIN = 0.05
MIN_ODDS = Decimal("1.01")

SEED_CREDITS = Decimal("1000.00")
MIN_STAKE = Decimal("10.00")
MAX_STAKE = Decimal("500.00")

DEFAULT_GOAL_BAND_ODDS = Decimal("4.50")

DEFAULT_SCORING_RULES: dict[str, int] = {
    "outcome": 3,
    "exact_score": 5,
    "goal_band": 2,
}
