from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from sqlalchemy import Select, and_, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import SessionPolicy
from db.models import Click, Session as SessionRow, User

logger = logging.getLogger(__name__)


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


_default_clock = SystemClock()


async def ensure_user(
    db: AsyncSession,
    *,
    tg_user_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> int:
    stmt = select(User.id).where(User.tg_user_id == tg_user_id)
    existing_id = (await db.execute(stmt)).scalar_one_or_none()
    if existing_id is not None:
        return existing_id

    user = User(
        tg_user_id=tg_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    await db.flush()
    return user.id


async def _acquire_user_lock(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        text("SELECT pg_advisory_xact_lock(:key)").bindparams(key=user_id)
    )


async def record_click(
    db: AsyncSession,
    *,
    user_id: int,
    policy: SessionPolicy,
    dialog_window: str | None,
    dialog_button: str | None,
    weight: int = 1,
    clock: Clock = _default_clock,
) -> int:
    """Record a click, creating / extending / rotating the user's session.

    Returns the session id the click was attached to. Commits nothing —
    caller owns the transaction boundary.
    """
    now = clock.now()
    await _acquire_user_lock(db, user_id)

    open_stmt: Select = (
        select(SessionRow)
        .where(
            and_(
                SessionRow.user_id == user_id,
                SessionRow.is_closed.is_(False),
            )
        )
        .with_for_update()
    )
    current = (await db.execute(open_stmt)).scalar_one_or_none()

    if current is not None and now > current.open_until_at:
        current.is_closed = True
        current.closed_at = current.last_activity_at + timedelta(
            minutes=current.close_after_last_activity_minutes
        )
        await db.flush()
        current = None

    if current is None:
        new_session = SessionRow(
            user_id=user_id,
            created_at=now,
            last_activity_at=now,
            open_until_at=now + timedelta(minutes=policy.extension_window_minutes),
            is_closed=False,
            closed_at=None,
            extension_window_minutes=policy.extension_window_minutes,
            close_after_last_activity_minutes=policy.close_after_last_activity_minutes,
        )
        db.add(new_session)
        await db.flush()
        session_id = new_session.id
    else:
        current.last_activity_at = now
        current.open_until_at = now + timedelta(minutes=current.extension_window_minutes)
        session_id = current.id

    db.add(
        Click(
            session_id=session_id,
            created_at=now,
            dialog_window=dialog_window,
            dialog_button=dialog_button,
            weight=weight,
        )
    )
    await db.flush()
    return session_id


async def close_stale_sessions(
    db: AsyncSession,
    *,
    clock: Clock = _default_clock,
) -> int:
    """Close every open session whose extension window has already passed.

    Idempotent — the WHERE clause skips already-closed rows. Returns the
    number of rows updated.
    """
    now = clock.now()
    stmt = (
        update(SessionRow)
        .where(
            and_(
                SessionRow.is_closed.is_(False),
                SessionRow.open_until_at < now,
            )
        )
        .values(
            is_closed=True,
            closed_at=SessionRow.last_activity_at
            + func.make_interval(0, 0, 0, 0, 0, SessionRow.close_after_last_activity_minutes, 0),
        )
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    return result.rowcount or 0


@dataclass(frozen=True)
class CoreKPI:
    active_users: int
    sessions_count: int
    clicks_count: int
    avg_session_duration_minutes: float | None
    avg_clicks_per_session: float | None


async def get_core_kpi(
    db: AsyncSession,
    *,
    start_utc: datetime,
    end_utc: datetime,
) -> CoreKPI:
    """Core activity KPIs over [start_utc, end_utc).

    Sessions are attributed by created_at; duration metric is restricted to
    closed sessions to keep it well-defined.
    """
    sess_window = and_(
        SessionRow.created_at >= start_utc,
        SessionRow.created_at < end_utc,
    )
    clicks_window = and_(
        Click.created_at >= start_utc,
        Click.created_at < end_utc,
    )

    active_users = (
        await db.execute(
            select(func.count(func.distinct(SessionRow.user_id))).where(sess_window)
        )
    ).scalar_one()

    sessions_count = (
        await db.execute(select(func.count()).select_from(SessionRow).where(sess_window))
    ).scalar_one()

    clicks_count = (
        await db.execute(select(func.count()).select_from(Click).where(clicks_window))
    ).scalar_one()

    duration_seconds = func.extract("epoch", SessionRow.closed_at - SessionRow.created_at)
    avg_duration_seconds = (
        await db.execute(
            select(func.avg(duration_seconds)).where(
                and_(sess_window, SessionRow.is_closed.is_(True))
            )
        )
    ).scalar_one()

    avg_clicks = (
        (clicks_count / sessions_count) if sessions_count else None
    )

    return CoreKPI(
        active_users=int(active_users or 0),
        sessions_count=int(sessions_count or 0),
        clicks_count=int(clicks_count or 0),
        avg_session_duration_minutes=(
            float(avg_duration_seconds) / 60.0 if avg_duration_seconds is not None else None
        ),
        avg_clicks_per_session=avg_clicks,
    )


@dataclass(frozen=True)
class DialogWindowStat:
    dialog_window: str | None
    clicks: int
    unique_users: int


async def get_top_dialog_windows(
    db: AsyncSession,
    *,
    start_utc: datetime,
    end_utc: datetime,
    limit: int = 10,
) -> list[DialogWindowStat]:
    stmt = (
        select(
            Click.dialog_window,
            func.count().label("clicks"),
            func.count(func.distinct(SessionRow.user_id)).label("unique_users"),
        )
        .join(SessionRow, SessionRow.id == Click.session_id)
        .where(
            and_(
                Click.created_at >= start_utc,
                Click.created_at < end_utc,
            )
        )
        .group_by(Click.dialog_window)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [
        DialogWindowStat(
            dialog_window=row.dialog_window,
            clicks=int(row.clicks),
            unique_users=int(row.unique_users),
        )
        for row in rows
    ]
