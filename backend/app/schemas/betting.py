from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.engine.selection import Selection
from app.models.bet import BetMarket, BetStatus
from app.models.match import MatchStatus


class BetCreate(BaseModel):
    selection: Selection
    stake: Decimal


class BetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    market: BetMarket
    selection: dict[str, object]
    stake: Decimal
    odds_snapshot: Decimal
    status: BetStatus
    settled_at: datetime | None
    created_at: datetime


class PredictionIn(BaseModel):
    predicted_home_score: Annotated[int, Field(ge=0)]
    predicted_away_score: Annotated[int, Field(ge=0)]


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    predicted_home_score: int
    predicted_away_score: int
    points_awarded: int | None


class GoalIn(BaseModel):
    team_id: UUID
    minute: Annotated[int, Field(ge=0)]
    is_stoppage: bool = False


class ResultIn(BaseModel):
    home_score: Annotated[int, Field(ge=0)]
    away_score: Annotated[int, Field(ge=0)]
    goals: list[GoalIn] = []


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID
    minute: int
    is_stoppage: bool


class MatchResultRead(BaseModel):
    id: UUID
    home_team_id: UUID
    away_team_id: UUID
    status: MatchStatus
    home_score: int | None
    away_score: int | None
    goals: list[GoalRead]


class MatchUpcomingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    round_id: UUID
    home_team_id: UUID
    away_team_id: UUID
    home_team_name: str
    away_team_name: str
    kickoff_at: datetime
    odds_home: Decimal
    odds_draw: Decimal
    odds_away: Decimal
    goal_band_odds: dict[str, Decimal]
    my_prediction: PredictionRead | None
    my_bets: list[BetRead]


class LeaderboardEntryRead(BaseModel):
    user_id: UUID
    display_name: str
    points: int
    exact_scores: int
    balance: Decimal


class BetMatchRead(BaseModel):
    """Contexto del partido que acompana a cada apuesta del historial."""

    home_team_name: str
    away_team_name: str
    kickoff_at: datetime
    status: MatchStatus
    home_score: int | None
    away_score: int | None


class BetWithMatchRead(BetRead):
    match: BetMatchRead


class SeasonSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str
    starts_on: date
    ends_on: date
