from __future__ import annotations

import inspect
import logging
from typing import Any, Callable

from aiogram.fsm.state import State
from aiogram_dialog import DialogManager, Window as AiogramDialogWindow
from aiogram.types import User as TgUser

from config.config import SessionPolicy, load_config
from db import async_session_factory
from service import ensure_user, record_click

logger = logging.getLogger(__name__)
_SESSION_POLICY: SessionPolicy | None = None


def _get_session_policy() -> SessionPolicy:
    global _SESSION_POLICY
    if _SESSION_POLICY is None:
        _SESSION_POLICY = load_config().session_policy
    return _SESSION_POLICY


def _state_to_string(state: State | str | None) -> str | None:
    if state is None:
        return None
    if isinstance(state, str):
        return state
    state_value = getattr(state, "state", None)
    if isinstance(state_value, str):
        return state_value
    return str(state)


def _extract_event_user(dialog_manager: DialogManager) -> TgUser | None:
    event = getattr(dialog_manager, "event", None)
    if event is not None:
        from_user = getattr(event, "from_user", None)
        if from_user is not None:
            return from_user

        update_obj = getattr(event, "update", None)
        if update_obj is not None:
            callback_query = getattr(update_obj, "callback_query", None)
            if callback_query is not None and callback_query.from_user is not None:
                return callback_query.from_user

            message = getattr(update_obj, "message", None)
            if message is not None and message.from_user is not None:
                return message.from_user

    middleware_user = dialog_manager.middleware_data.get("event_from_user")
    if middleware_user is not None:
        return middleware_user

    return None


async def _record_getter_click(
    dialog_manager: DialogManager,
    *,
    state: State | str | None,
) -> None:
    user = _extract_event_user(dialog_manager)
    if user is None:
        return

    dialog_window = _state_to_string(state)

    try:
        async with async_session_factory() as db:
            user_id = await ensure_user(
                db,
                tg_user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            await record_click(
                db,
                user_id=user_id,
                policy=_get_session_policy(),
                dialog_window=dialog_window,
                dialog_button=None,
            )
            await db.commit()
    except Exception:
        logger.exception("failed to record getter click for state=%s", dialog_window)


async def _empty_getter(_: DialogManager, **__: Any) -> dict[str, Any]:
    return {}


def _wrap_getter(
    getter: Callable[..., Any] | None,
    *,
    state: State | str | None,
) -> Callable[..., Any]:
    base_getter = getter or _empty_getter

    async def _tracked_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
        result = base_getter(dialog_manager, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        await _record_getter_click(dialog_manager, state=state)
        if result is None:
            return {}
        return result

    return _tracked_getter


class Window(AiogramDialogWindow):
    def __init__(
        self,
        *widgets: Any,
        getter: Callable[..., Any] | None = None,
        state: State | str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *widgets,
            getter=_wrap_getter(getter, state=state),
            state=state,
            **kwargs,
        )

