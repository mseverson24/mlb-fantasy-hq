import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPkMixin
from app.models.platform_account import Platform


class League(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "leagues"
    __table_args__ = (
        UniqueConstraint("platform", "platform_league_id", "season", name="uq_league_platform_external_season"),
    )

    platform: Mapped[Platform] = mapped_column(SAEnum(Platform, name="platform_enum"), nullable=False)
    platform_league_id: Mapped[str] = mapped_column(String(100), nullable=False)
    season: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Points vs. rotisserie/categories -- stored for display only in V1, not
    # yet used to compute standings from scratch (CBS's own standings page
    # is scraped directly instead, see integrations/cbs).
    scoring_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    num_teams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # MLB slot vocabulary (C/1B/2B/3B/SS/OF/DH/SP/RP/UTIL/BN/IL), not the NFL
    # sibling app's FLEX/SUPER_FLEX slots.
    roster_positions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    teams: Mapped[list["Team"]] = relationship(back_populates="league", cascade="all, delete-orphan")
    league_links: Mapped[list["LeagueLink"]] = relationship(back_populates="league", cascade="all, delete-orphan")


class LeagueLink(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "league_links"
    __table_args__ = (UniqueConstraint("league_id", "user_id", name="uq_league_link_league_user"),)

    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    league: Mapped["League"] = relationship(back_populates="league_links")
    user: Mapped["User"] = relationship()
    platform_account: Mapped["PlatformAccount"] = relationship(back_populates="league_links")


class Team(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "teams"

    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform_team_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_my_team: Mapped[bool] = mapped_column(default=False, nullable=False)

    league: Mapped["League"] = relationship(back_populates="teams")
    rosters: Mapped[list["Roster"]] = relationship(back_populates="team", cascade="all, delete-orphan")


class Roster(UUIDPkMixin, TimestampMixin, Base):
    """A team's player list. week is None for the live/current roster
    snapshot -- same convention the NFL sibling app uses, kept here even
    though MLB has no real concept of a weekly roster lock, for a cheap
    future "roster as of date X" extension without a schema change."""

    __tablename__ = "rosters"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week: Mapped[int | None] = mapped_column(Integer, nullable=True)

    team: Mapped["Team"] = relationship(back_populates="rosters")
    roster_players: Mapped[list["RosterPlayer"]] = relationship(back_populates="roster", cascade="all, delete-orphan")


class RosterPlayer(Base):
    __tablename__ = "roster_players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rosters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slot: Mapped[str | None] = mapped_column(String(20), nullable=True)

    roster: Mapped["Roster"] = relationship(back_populates="roster_players")
    player: Mapped["Player"] = relationship()
