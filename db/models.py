from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=True)
    tg_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    max_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amo_contact_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    amo_deal_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_term: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    yclid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_parameter: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    notification_stage: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    current_state: Mapped[str | None] = mapped_column(String(255), nullable=True)

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    open_until_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    extension_window_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    close_after_last_activity_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")
    clicks: Mapped[list["Click"]] = relationship("Click", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "(is_closed = false AND closed_at IS NULL) OR (is_closed = true AND closed_at IS NOT NULL)",
            name="ck_sessions_closed_state",
        ),
        Index(
            "uq_sessions_one_open_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("is_closed = false"),
        ),
        Index(
            "ix_sessions_sweeper_open_until",
            "open_until_at",
            postgresql_where=text("is_closed = false"),
        ),
    )

    @hybrid_property
    def total_duration_minutes(self) -> float:
        end = self.closed_at or _utcnow()
        start = self.created_at
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        return (end - start).total_seconds() / 60


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    dialog_window: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dialog_button: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    session: Mapped["Session"] = relationship("Session", back_populates="clicks")

    __table_args__ = (
        Index("ix_clicks_session_created", "session_id", "created_at"),
        Index("ix_clicks_dialog_window_created", "dialog_window", "created_at"),
    )
