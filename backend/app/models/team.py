import uuid

from sqlalchemy import CheckConstraint, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (CheckConstraint("strength BETWEEN 1 AND 100", name="ck_teams_strength_range"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    strength: Mapped[int] = mapped_column(nullable=False)
    crest_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
