import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPkMixin


class Platform(str, enum.Enum):
    cbs = "cbs"


class PlatformAccount(UUIDPkMixin, TimestampMixin, Base):
    """A linked external account. For CBS (the only platform today — no
    public OAuth exists), access_token holds the session cookie/token
    produced by a one-time login (see integrations/cbs/adapter.py's
    resolve_login), never the raw password itself -- same convention the
    sibling NFL app's MFL integration already established for a
    password-login platform with no OAuth.
    """

    __tablename__ = "platform_accounts"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "platform", "external_user_id", name="uq_platform_account_user_platform_external"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[Platform] = mapped_column(SAEnum(Platform, name="platform_enum"), nullable=False)
    external_user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    access_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    user: Mapped["User"] = relationship(back_populates="platform_accounts")
    league_links: Mapped[list["LeagueLink"]] = relationship(
        back_populates="platform_account", cascade="all, delete-orphan"
    )
