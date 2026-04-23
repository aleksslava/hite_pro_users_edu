from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import StartMode
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent
from aiogram_dialog.api.protocols import BgManagerFactory
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


def _extract_chat_context(event: Any) -> tuple[int | None, int | None, str | None]:
    if isinstance(event, Message):
        return (
            event.chat.id,
            event.message_thread_id,
            event.business_connection_id,
        )

    if isinstance(event, CallbackQuery):
        message = event.message
        if message is None:
            return None, None, None
        chat = getattr(message, "chat", None)
        if chat is None:
            return None, None, None
        return (
            chat.id,
            getattr(message, "message_thread_id", None),
            getattr(message, "business_connection_id", None),
        )

    return None, None, None


class StatePersistenceMiddleware(BaseMiddleware):
    def __init__(
        self,
        *,
        enable_restore: bool = True,
        enable_persist: bool = True,
        bg_factory: BgManagerFactory | None = None,
    ) -> None:
        self._enable_restore = enable_restore
        self._enable_persist = enable_persist
        self._bg_factory = bg_factory

    def set_bg_factory(self, bg_factory: BgManagerFactory) -> None:
        self._bg_factory = bg_factory

    async def _start_state(
        self,
        *,
        event: Any,
        data: dict[str, Any],
        tg_user_id: int,
        state_obj: Any,
    ) -> bool:
        dm = data.get("dialog_manager")
        if dm is not None:
            await dm.start(state_obj, mode=StartMode.RESET_STACK)
            return True

        if self._bg_factory is None:
            return False

        bot = data.get("bot")
        if not isinstance(bot, Bot):
            return False

        chat_id, thread_id, business_connection_id = _extract_chat_context(event)
        if chat_id is None:
            return False

        bg = self._bg_factory.bg(
            bot=bot,
            user_id=tg_user_id,
            chat_id=chat_id,
            thread_id=thread_id,
            business_connection_id=business_connection_id,
        )
        await bg.start(state_obj, mode=StartMode.RESET_STACK)
        return True

    async def _try_restore(
        self,
        *,
        event: Any,
        data: dict[str, Any],
        tg_user_id: int,
        fallback: bool = False,
    ) -> bool:
        try:
            saved = await _load_saved_state(tg_user_id)
            state_obj = resolve_state(saved)
            if state_obj is None:
                if not fallback:
                    return False
                state_obj = MainDialog.main_menu

            restored = await self._start_state(
                event=event,
                data=data,
                tg_user_id=tg_user_id,
                state_obj=state_obj,
            )
            if not restored:
                logger.warning(
                    "state restore skipped for tg_user_id=%s: no manager context",
                    tg_user_id,
                )
            return restored
        except Exception:
            logger.exception("state restore failed for tg_user_id=%s", tg_user_id)
            return False

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None)
        tg_user_id = getattr(from_user, "id", None)

        if self._enable_restore and tg_user_id is not None:
            needs_restore = isinstance(event, CallbackQuery)
            if isinstance(event, Message):
                text = (event.text or "").strip()
                needs_restore = not text.startswith("/")
            if needs_restore:
                try:
                    current_state = await _read_current_state(data)
                    if current_state is None:
                        await self._try_restore(
                            event=event,
                            data=data,
                            tg_user_id=tg_user_id,
                        )
                except Exception:
                    logger.exception("proactive restore check failed")

        result = None
        try:
            result = await handler(event, data)
        except (UnknownIntent, OutdatedIntent):
            if self._enable_restore and tg_user_id is not None:
                logger.info(
                    "Unknown/Outdated intent for tg_user_id=%s, restoring",
                    tg_user_id,
                )
                await self._try_restore(
                    event=event,
                    data=data,
                    tg_user_id=tg_user_id,
                    fallback=True,
                )
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer()
                    except Exception:
                        logger.exception("failed to answer outdated callback")
            else:
                raise

        if self._enable_persist and tg_user_id is not None:
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
