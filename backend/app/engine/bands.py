from enum import StrEnum


class GoalBand(StrEnum):
    MIN_0_15 = "0-15"
    MIN_16_30 = "16-30"
    MIN_31_45 = "31-45"
    MIN_46_60 = "46-60"
    MIN_61_75 = "61-75"
    MIN_76_90_PLUS = "76-90+"


def band_for_minute(minute: int, is_stoppage: bool) -> GoalBand:
    if is_stoppage:
        return GoalBand.MIN_76_90_PLUS
    if minute <= 15:
        return GoalBand.MIN_0_15
    if minute <= 30:
        return GoalBand.MIN_16_30
    if minute <= 45:
        return GoalBand.MIN_31_45
    if minute <= 60:
        return GoalBand.MIN_46_60
    if minute <= 75:
        return GoalBand.MIN_61_75
    return GoalBand.MIN_76_90_PLUS
