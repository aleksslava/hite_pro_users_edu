from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import StartMode
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent
from sqlalchemy import select

from db import async_session_factory
from db.models import User
from fsm_forms.fsm_models import MainDialog
from fsm_forms.state_registry import resolve_state
from service import ensure_user, update_user_current_state

logger = logging.getLogger(__name__)


def _read_dialog_state(data: dict[str, Any]) -> str | None:
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


async def _read_current_state(data: dict[str, Any]) -> str | None:
    dialog_state = _read_dialog_state(data)
    if dialog_state is not None:
        return dialog_state

    raw_state = data.get("raw_state")
    if isinstance(raw_state, str):
        return raw_state

    fsm_ctx: FSMContext | None = data.get("state")
    if fsm_ctx is None:
        return None
    try:
        return await fsm_ctx.get_state()
    except Exception:
        return None


async def _load_saved_state(tg_user_id: int) -> str | None:
    async with async_session_factory() as db:
        result = await db.execute(
            select(User.current_state).where(User.tg_user_id == tg_user_id)
        )
        return result.scalar_one_or_none()


async def _try_restore(dm: Any, tg_user_id: int, *, fallback: bool = False) -> None:
    try:
        saved = await _load_saved_state(tg_user_id)
        state_obj = resolve_state(saved)
        if state_obj is None:
            if not fallback:
                return
            state_obj = MainDialog.main_menu
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

        if dm is not None and tg_user_id is not None:
            needs_restore = isinstance(event, CallbackQuery)
            if isinstance(event, Message):
                text = (event.text or "").strip()
                needs_restore = not text.startswith("/")
            if needs_restore:
                try:
                    current_state = await _read_current_state(data)
                    if current_state is None:
                        await _try_restore(dm, tg_user_id)
                except Exception:
                    logger.exception("proactive restore check failed")

        result = None
        try:
            result = await handler(event, data)
        except (UnknownIntent, OutdatedIntent):
            logger.info("Unknown/Outdated intent for tg_user_id=%s, restoring", tg_user_id)
            if dm is not None and tg_user_id is not None:
                await _try_restore(dm, tg_user_id, fallback=True)

        if tg_user_id is not None:
            try:
                new_state = await _read_current_state(data)
                if new_state is not None:
                    async with async_session_factory() as db:
                        await ensure_user(
                            db,
                            tg_user_id=tg_user_id,
                            username=getattr(from_user, "username", None),
                            first_name=getattr(from_user, "first_name", None),
                            last_name=getattr(from_user, "last_name", None),
                        )
                        await update_user_current_state(
                            db,
                            tg_user_id=tg_user_id,
                            state=new_state,
                        )
                        await db.commit()
            except Exception:
                logger.exception("state persist failed")

        return result
