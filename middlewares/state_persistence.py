from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram_dialog import StartMode
from aiogram_dialog.api.exceptions import UnknownIntent
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


async def _try_restore(dm: Any, tg_user_id: int) -> None:
    try:
        saved = await _load_saved_state(tg_user_id)
        state_obj = resolve_state(saved)
        if state_obj is not None:
            await dm.start(state_obj, mode=StartMode.RESET_STACK)
    except Exception:
        logger.exception("state restore failed for tg_user_id=%s", tg_user_id)


class StatePersistenceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        dm = data.get("dialog_manager")
        from_user = getattr(event, "from_user", None)
        tg_user_id = getattr(from_user, "id", None)

        if isinstance(event, Message) and dm is not None and tg_user_id is not None:
            try:
                fsm_ctx: FSMContext | None = data.get("state")
                current_fsm = await fsm_ctx.get_state() if fsm_ctx is not None else None
                if current_fsm is None:
                    await _try_restore(dm, tg_user_id)
            except Exception:
                logger.exception("proactive restore check failed")

        result = None
        try:
            result = await handler(event, data)
        except UnknownIntent:
            logger.info("UnknownIntent for tg_user_id=%s — restoring saved state", tg_user_id)
            if dm is not None and tg_user_id is not None:
                await _try_restore(dm, tg_user_id)

        if tg_user_id is not None:
            try:
                new_state = _extract_dialog_window(data)
                if new_state is not None:
                    async with async_session_factory() as db:
                        await update_user_current_state(
                            db, tg_user_id=tg_user_id, state=new_state
                        )
                        await db.commit()
            except Exception:
                logger.exception("state persist failed")

        return result
