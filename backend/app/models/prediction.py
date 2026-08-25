import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("user_id", "match_id", name="uq_predictions_user_id_match_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    predicted_home_score: Mapped[int] = mapped_column(nullable=False)
    predicted_away_score: Mapped[int] = mapped_column(nullable=False)
    points_awarded: Mapped[int | None] = mapped_column(nullable=True)
