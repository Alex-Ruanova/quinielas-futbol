import uuid
from decimal import Decimal

from sqlalchemy import Numeric, case, cast, func, select
from sqlalchemy.orm import Session

from app.models.credit_transaction import CreditTransaction
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.round import Round
from app.models.user import User


class LeaderboardRow:
    def __init__(
        self,
        user_id: uuid.UUID,
        display_name: str,
        points: int,
        exact_scores: int,
        balance: Decimal,
    ) -> None:
        self.user_id = user_id
        self.display_name = display_name
        self.points = points
        self.exact_scores = exact_scores
        self.balance = balance


def get_leaderboard(session: Session, season_id: uuid.UUID) -> list[LeaderboardRow]:
    exact_match = (
        (Prediction.predicted_home_score == Match.home_score)
        & (Prediction.predicted_away_score == Match.away_score)
        & (Match.home_score.is_not(None))
    )
    points_subquery = (
        select(
            Prediction.user_id.label("user_id"),
            func.coalesce(func.sum(Prediction.points_awarded), 0).label("points"),
            func.sum(case((exact_match, 1), else_=0)).label("exact_scores"),
        )
        .join(Match, Match.id == Prediction.match_id)
        .join(Round, Round.id == Match.round_id)
        .where(Round.season_id == season_id)
        .group_by(Prediction.user_id)
        .subquery()
    )
    balance_subquery = (
        select(
            CreditTransaction.user_id.label("user_id"),
            func.coalesce(func.sum(CreditTransaction.amount), 0).label("balance"),
        )
        .group_by(CreditTransaction.user_id)
        .subquery()
    )
    zero_balance = cast(0, Numeric(12, 2))

    stmt = (
        select(
            User.id,
            User.display_name,
            points_subquery.c.points,
            points_subquery.c.exact_scores,
            func.coalesce(balance_subquery.c.balance, zero_balance),
        )
        .join(points_subquery, points_subquery.c.user_id == User.id)
        .outerjoin(balance_subquery, balance_subquery.c.user_id == User.id)
        .order_by(
            points_subquery.c.points.desc(),
            points_subquery.c.exact_scores.desc(),
            func.coalesce(balance_subquery.c.balance, zero_balance).desc(),
        )
    )
    rows = session.execute(stmt).all()
    return [
        LeaderboardRow(
            user_id=row[0],
            display_name=row[1],
            points=int(row[2]),
            exact_scores=int(row[3]),
            balance=Decimal(row[4]),
        )
        for row in rows
    ]
