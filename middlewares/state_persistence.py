from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import StartMode
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent
from aiogram_dialog.api.protocols import BgManagerFactory

from db import async_session_factory
from fsm_forms.fsm_models import MainDialog
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

    async def _persist_state_for_user(
        self,
        *,
        tg_user_id: int,
        from_user: Any,
        state: str,
    ) -> None:
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
                state=state,
            )
            await db.commit()

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

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None)
        tg_user_id = getattr(from_user, "id", None)

        result = None
        try:
            result = await handler(event, data)
        except (UnknownIntent, OutdatedIntent):
            if (
                self._enable_restore
                and tg_user_id is not None
                and isinstance(event, CallbackQuery)
            ):
                logger.info(
                    "Unknown/Outdated intent for tg_user_id=%s, starting from main menu",
                    tg_user_id,
                )
                restarted = await self._start_state(
                    event=event,
                    data=data,
                    tg_user_id=tg_user_id,
                    state_obj=MainDialog.main_menu,
                )
                if not restarted:
                    logger.warning(
                        "failed to restart dialog for tg_user_id=%s: no manager context",
                        tg_user_id,
                    )
                else:
                    try:
                        await self._persist_state_for_user(
                            tg_user_id=tg_user_id,
                            from_user=from_user,
                            state=str(MainDialog.main_menu.state),
                        )
                    except Exception:
                        logger.exception("failed to persist /start state")
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
                    await self._persist_state_for_user(
                        tg_user_id=tg_user_id,
                        from_user=from_user,
                        state=new_state,
                    )
            except Exception:
                logger.exception("state persist failed")

        return result
