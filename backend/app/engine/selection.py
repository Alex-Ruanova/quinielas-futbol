from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .bands import GoalBand


class OutcomeSelection(BaseModel):
    model_config = ConfigDict(frozen=True)

    market: Literal["OUTCOME"] = "OUTCOME"
    pick: Literal["HOME", "DRAW", "AWAY"]


class GoalBandSelection(BaseModel):
    model_config = ConfigDict(frozen=True)

    market: Literal["GOAL_BAND"] = "GOAL_BAND"
    band: GoalBand
    team_id: UUID | None = None


Selection = Annotated[
    Union[OutcomeSelection, GoalBandSelection], Field(discriminator="market")
]
