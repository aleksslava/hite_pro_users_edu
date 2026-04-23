from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram_dialog import StartMode
from sqlalchemy import select

from db import async_session_factory
from db.models import User
from fsm_forms.state_registry import resolve_state
from service import update_user_current_state

logger = logging.getLogger(__name__)


def _extract_dialog_window(data: dict[str, Any]) -> str | None:
    dm = data.get("dialog_manager")
    if dm is None:
        return None
    try:
        state = dm.current_context().state
    except Exception:
        return None
    if state is None:
        return None
    return str(getattr(state, "state", state))


async def _load_saved_state(tg_user_id: int) -> str | None:
    async with async_session_factory() as db:
        result = await db.execute(
            select(User.current_state).where(User.tg_user_id == tg_user_id)
        )
        return result.scalar_one_or_none()


class StatePersistenceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        dm = data.get("dialog_manager")
        from_user = getattr(event, "from_user", None)

        if dm is not None and from_user is not None:
            try:
                has_context = False
                try:
                    has_context = dm.current_context() is not None
                except Exception:
                    has_context = False
                if not has_context:
                    saved = await _load_saved_state(from_user.id)
                    state_obj = resolve_state(saved)
                    if state_obj is not None:
                        await dm.start(state_obj, mode=StartMode.RESET_STACK)
            except Exception:
                logger.exception("state restore failed")

        result = await handler(event, data)

        if from_user is not None:
            try:
                new_state = _extract_dialog_window(data)
                async with async_session_factory() as db:
                    await update_user_current_state(
                        db, tg_user_id=from_user.id, state=new_state
                    )
                    await db.commit()
            except Exception:
                logger.exception("state persist failed")

        return result
