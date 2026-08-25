from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_session
from app.schemas.catalog import (
    MatchCreate,
    MatchRead,
    MatchUpdate,
    OddsPreview,
    RoundCreate,
    RoundRead,
    RoundUpdate,
    ScoringConfigUpdate,
    SeasonCreate,
    SeasonRead,
    SeasonUpdate,
    TeamCreate,
    TeamRead,
    TeamUpdate,
)
from app.services import catalog as catalog_service

router = APIRouter(
    prefix="/api/v1/admin",
    dependencies=[Depends(require_admin)],
)

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/teams", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(data: TeamCreate, session: SessionDep) -> TeamRead:
    team = catalog_service.create_team(session, data)
    session.commit()
    return TeamRead.model_validate(team)


@router.get("/teams", response_model=list[TeamRead])
def list_teams(session: SessionDep) -> list[TeamRead]:
    teams = catalog_service.list_teams(session)
    return [TeamRead.model_validate(team) for team in teams]


@router.get("/teams/{team_id}", response_model=TeamRead)
def get_team(team_id: UUID, session: SessionDep) -> TeamRead:
    team = catalog_service.get_team(session, team_id)
    return TeamRead.model_validate(team)


@router.patch("/teams/{team_id}", response_model=TeamRead)
def update_team(team_id: UUID, data: TeamUpdate, session: SessionDep) -> TeamRead:
    team = catalog_service.update_team(session, team_id, data)
    session.commit()
    return TeamRead.model_validate(team)


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: UUID, session: SessionDep) -> None:
    catalog_service.delete_team(session, team_id)
    session.commit()


@router.get("/teams/{team_id}/odds-preview", response_model=OddsPreview)
def team_odds_preview(
    team_id: UUID,
    session: SessionDep,
    opponent_strength: Annotated[int, Query(ge=1, le=100)],
) -> OddsPreview:
    odds = catalog_service.team_odds_preview(session, team_id, opponent_strength)
    return OddsPreview.model_validate(odds, from_attributes=True)


@router.post("/seasons", response_model=SeasonRead, status_code=status.HTTP_201_CREATED)
def create_season(data: SeasonCreate, session: SessionDep) -> SeasonRead:
    season = catalog_service.create_season(session, data)
    session.commit()
    return SeasonRead.model_validate(season)


@router.get("/seasons", response_model=list[SeasonRead])
def list_seasons(session: SessionDep) -> list[SeasonRead]:
    seasons = catalog_service.list_seasons(session)
    return [SeasonRead.model_validate(season) for season in seasons]


@router.get("/seasons/{season_id}", response_model=SeasonRead)
def get_season(season_id: UUID, session: SessionDep) -> SeasonRead:
    season = catalog_service.get_season(session, season_id)
    return SeasonRead.model_validate(season)


@router.patch("/seasons/{season_id}", response_model=SeasonRead)
def update_season(
    season_id: UUID, data: SeasonUpdate, session: SessionDep
) -> SeasonRead:
    season = catalog_service.update_season(session, season_id, data)
    session.commit()
    return SeasonRead.model_validate(season)


@router.patch("/seasons/{season_id}/scoring", response_model=SeasonRead)
def update_scoring_config(
    season_id: UUID, data: ScoringConfigUpdate, session: SessionDep
) -> SeasonRead:
    season = catalog_service.update_scoring_config(session, season_id, data)
    session.commit()
    return SeasonRead.model_validate(season)


@router.delete("/seasons/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_season(season_id: UUID, session: SessionDep) -> None:
    catalog_service.delete_season(session, season_id)
    session.commit()


@router.post("/rounds", response_model=RoundRead, status_code=status.HTTP_201_CREATED)
def create_round(data: RoundCreate, session: SessionDep) -> RoundRead:
    round_ = catalog_service.create_round(session, data)
    session.commit()
    return RoundRead.model_validate(round_)


@router.get("/rounds", response_model=list[RoundRead])
def list_rounds(session: SessionDep, season_id: UUID | None = None) -> list[RoundRead]:
    rounds = catalog_service.list_rounds(session, season_id)
    return [RoundRead.model_validate(round_) for round_ in rounds]


@router.get("/rounds/{round_id}", response_model=RoundRead)
def get_round(round_id: UUID, session: SessionDep) -> RoundRead:
    round_ = catalog_service.get_round(session, round_id)
    return RoundRead.model_validate(round_)


@router.patch("/rounds/{round_id}", response_model=RoundRead)
def update_round(round_id: UUID, data: RoundUpdate, session: SessionDep) -> RoundRead:
    round_ = catalog_service.update_round(session, round_id, data)
    session.commit()
    return RoundRead.model_validate(round_)


@router.delete("/rounds/{round_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_round(round_id: UUID, session: SessionDep) -> None:
    catalog_service.delete_round(session, round_id)
    session.commit()


@router.post("/matches", response_model=MatchRead, status_code=status.HTTP_201_CREATED)
def create_match(data: MatchCreate, session: SessionDep) -> MatchRead:
    match = catalog_service.create_match(session, data)
    session.commit()
    return MatchRead.model_validate(match)


@router.get("/matches", response_model=list[MatchRead])
def list_matches(session: SessionDep, round_id: UUID | None = None) -> list[MatchRead]:
    matches = catalog_service.list_matches(session, round_id)
    return [MatchRead.model_validate(match) for match in matches]


@router.get("/matches/{match_id}", response_model=MatchRead)
def get_match(match_id: UUID, session: SessionDep) -> MatchRead:
    match = catalog_service.get_match(session, match_id)
    return MatchRead.model_validate(match)


@router.patch("/matches/{match_id}", response_model=MatchRead)
def update_match(match_id: UUID, data: MatchUpdate, session: SessionDep) -> MatchRead:
    match = catalog_service.update_match(session, match_id, data)
    session.commit()
    return MatchRead.model_validate(match)


@router.delete("/matches/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(match_id: UUID, session: SessionDep) -> None:
    catalog_service.delete_match(session, match_id)
    session.commit()
