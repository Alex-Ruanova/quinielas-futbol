import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BetMarket(str, enum.Enum):
    OUTCOME = "OUTCOME"
    GOAL_BAND = "GOAL_BAND"


class BetStatus(str, enum.Enum):
    PENDING = "PENDING"
    WON = "WON"
    LOST = "LOST"
    VOID = "VOID"


class Bet(Base):
    __tablename__ = "bets"
    __table_args__ = (Index("ix_bets_match_id_status", "match_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    market: Mapped[BetMarket] = mapped_column(Enum(BetMarket, name="bet_market"), nullable=False)
    selection: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    stake: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    odds_snapshot: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    status: Mapped[BetStatus] = mapped_column(
        Enum(BetStatus, name="bet_status"), nullable=False, default=BetStatus.PENDING
    )
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
