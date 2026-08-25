from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.engine.bands import GoalBand
from app.engine.config import MIN_ODDS
from app.models.match import MatchStatus

Strength = Annotated[int, Field(ge=1, le=100)]


class TeamCreate(BaseModel):
    name: str
    strength: Strength
    crest_url: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = None
    strength: Strength | None = None
    crest_url: str | None = None


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    strength: int
    crest_url: str | None


class SeasonCreate(BaseModel):
    name: str
    starts_on: date
    ends_on: date
    scoring_config: dict[str, object] | None = None

    @model_validator(mode="after")
    def _dates_ordered(self) -> "SeasonCreate":
        if self.ends_on < self.starts_on:
            raise ValueError("ends_on must not be before starts_on")
        return self


class SeasonUpdate(BaseModel):
    name: str | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    status: str | None = None


class SeasonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    starts_on: date
    ends_on: date
    scoring_config: dict[str, object] | None
    status: str


class ScoringConfigUpdate(BaseModel):
    """Partial update, merged key-by-key against DEFAULT_SCORING_RULES / DEFAULT_GOAL_BAND_ODDS."""

    outcome: Annotated[int, Field(ge=0)] | None = None
    exact_score: Annotated[int, Field(ge=0)] | None = None
    goal_band: Annotated[int, Field(ge=0)] | None = None
    goal_band_odds: dict[GoalBand, Decimal] | None = None

    @field_validator("goal_band_odds")
    @classmethod
    def _odds_within_range(
        cls, value: dict[GoalBand, Decimal] | None
    ) -> dict[GoalBand, Decimal] | None:
        if value is None:
            return value
        for band, odds in value.items():
            if odds < MIN_ODDS:
                raise ValueError(f"odds for band {band} must be >= {MIN_ODDS}")
        return value


class RoundCreate(BaseModel):
    season_id: UUID
    number: int
    name: str
    opens_at: datetime
    closes_at: datetime

    @model_validator(mode="after")
    def _window_ordered(self) -> "RoundCreate":
        if self.closes_at <= self.opens_at:
            raise ValueError("closes_at must be after opens_at")
        return self


class RoundUpdate(BaseModel):
    number: int | None = None
    name: str | None = None
    opens_at: datetime | None = None
    closes_at: datetime | None = None


class RoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    season_id: UUID
    number: int
    name: str
    opens_at: datetime
    closes_at: datetime


class MatchCreate(BaseModel):
    round_id: UUID
    home_team_id: UUID
    away_team_id: UUID
    kickoff_at: datetime


class MatchUpdate(BaseModel):
    round_id: UUID | None = None
    home_team_id: UUID | None = None
    away_team_id: UUID | None = None
    kickoff_at: datetime | None = None
    status: MatchStatus | None = None


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    round_id: UUID
    home_team_id: UUID
    away_team_id: UUID
    kickoff_at: datetime
    status: MatchStatus
    home_score: int | None
    away_score: int | None
    settled_at: datetime | None


class OddsPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    odds_home: Decimal
    odds_draw: Decimal
    odds_away: Decimal
