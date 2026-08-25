from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config import DEFAULT_SCORING_RULES
from .errors import InvalidSelection


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

    outcome: Annotated[int, Field(ge=0)]
    exact_score: Annotated[int, Field(ge=0)]
    goal_band: Annotated[int, Field(ge=0)]

    @classmethod
    def from_config(cls, raw: dict[str, Any] | None) -> "ScoringRules":
        """Construye las reglas desde el `scoring_config` JSONB, clave por clave."""
        known = {k: v for k, v in (raw or {}).items() if k in DEFAULT_SCORING_RULES}
        try:
            return cls(**{**DEFAULT_SCORING_RULES, **known})
        except ValidationError as exc:
            # El JSONB no está tipado por la base: un valor corrupto tiene que salir
            # como error de dominio (A4), no como un 500 de Pydantic.
            raise InvalidSelection(f"scoring_config inválido: {exc.errors()}") from exc


def score_prediction(predicted: Score, actual: Score, rules: ScoringRules) -> int:
    if predicted.winner() != actual.winner():
        return 0
    points = rules.outcome
    if predicted.home == actual.home and predicted.away == actual.away:
        points += rules.exact_score
    return points
