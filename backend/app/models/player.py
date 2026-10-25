from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPkMixin


class Player(UUIDPkMixin, TimestampMixin, Base):
    """An MLB player. Deliberately no cross-platform id columns beyond CBS
    for V1 (the sibling NFL app's Player row carries one nullable id column
    per linked platform plus cross-platform name-matching, needed there
    because a league might be synced from Sleeper while rankings come from
    CBS/ESPN/etc. -- V1 here has exactly one real data source, so that
    complexity has nothing to resolve yet. Add it if/when a second MLB
    platform (Yahoo, ESPN) is wired in."""

    __tablename__ = "players"

    full_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    # MLB vocabulary: C, 1B, 2B, 3B, SS, OF, DH, SP, RP -- not the NFL
    # sibling app's QB/RB/WR/TE/etc.
    position: Mapped[str | None] = mapped_column(String(10), nullable=True)
    mlb_team: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cbs_player_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    injury_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
