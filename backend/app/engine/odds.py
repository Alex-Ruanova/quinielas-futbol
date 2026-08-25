from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, ConfigDict

from .config import DRAW_BASE, HOME_ADVANTAGE, MARGIN, MIN_ODDS

CENTS = Decimal("0.01")


class OddsConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    home_advantage: float = HOME_ADVANTAGE
    draw_base: float = DRAW_BASE
    margin: float = MARGIN
    min_odds: Decimal = MIN_ODDS


class MatchOdds(BaseModel):
    model_config = ConfigDict(frozen=True)

    odds_home: Decimal
    odds_draw: Decimal
    odds_away: Decimal


def _odds_from_probability(probability: float, config: OddsConfig) -> Decimal:
    raw = Decimal(str((1 - config.margin) / probability)).quantize(
        CENTS, rounding=ROUND_HALF_UP
    )
    return max(config.min_odds, raw)


def compute_odds(strength_home: int, strength_away: int, config: OddsConfig) -> MatchOdds:
    sh = strength_home * (1 + config.home_advantage)
    sa = float(strength_away)

    p_home_raw = sh / (sh + sa)
    p_draw = config.draw_base * (1 - abs(sh - sa) / (sh + sa))
    p_home = (1 - p_draw) * p_home_raw
    p_away = (1 - p_draw) * (1 - p_home_raw)

    return MatchOdds(
        odds_home=_odds_from_probability(p_home, config),
        odds_draw=_odds_from_probability(p_draw, config),
        odds_away=_odds_from_probability(p_away, config),
    )
