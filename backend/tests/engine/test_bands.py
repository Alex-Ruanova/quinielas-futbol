from app.engine.bands import GoalBand, band_for_minute


def test_stoppage_time_falls_in_last_band() -> None:
    assert band_for_minute(90, is_stoppage=True) == GoalBand.MIN_76_90_PLUS


def test_minute_46_falls_in_46_60() -> None:
    assert band_for_minute(46, is_stoppage=False) == GoalBand.MIN_46_60


def test_minute_45_falls_in_31_45() -> None:
    assert band_for_minute(45, is_stoppage=False) == GoalBand.MIN_31_45
