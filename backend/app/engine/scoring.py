from pydantic import BaseModel, ConfigDict

from .config import DEFAULT_SCORING_RULES


class Score(BaseModel):
    model_config = ConfigDict(frozen=True)

    home: int
    away: int

    def winner(self) -> str:
        if self.home > self.away:
            return "HOME"
        if self.away > self.home:
            return "AWAY"
        return "DRAW"


class ScoringRules(BaseModel):
    model_config = ConfigDict(frozen=True)

    outcome: int
    exact_score: int
    goal_band: int

    @classmethod
    def from_config(cls, raw: dict | None) -> "ScoringRules":
        merged = {**DEFAULT_SCORING_RULES, **(raw or {})}
        return cls(**merged)


def score_prediction(predicted: Score, actual: Score, rules: ScoringRules) -> int:
    if predicted.winner() != actual.winner():
        return 0
    points = rules.outcome
    if predicted.home == actual.home and predicted.away == actual.away:
        points += rules.exact_score
    return points
