from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from config.config import SessionPolicy
from db import async_session_factory
from service import ensure_user, record_click

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


class ClickTrackingMiddleware(BaseMiddleware):
    def __init__(self, policy: SessionPolicy) -> None:
        self._policy = policy

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        data["session_policy"] = self._policy
        result = await handler(event, data)
        if event.from_user is not None:
            dialog_window = _extract_dialog_window(data)
            dialog_button = event.data
            try:
                async with async_session_factory() as db:
                    user_id = await ensure_user(
                        db,
                        tg_user_id=event.from_user.id,
                        username=event.from_user.username,
                        first_name=event.from_user.first_name,
                        last_name=event.from_user.last_name,
                    )
                    await record_click(
                        db,
                        user_id=user_id,
                        policy=self._policy,
                        dialog_window=dialog_window,
                        dialog_button=dialog_button,
                    )
                    await db.commit()
            except Exception:
                logger.exception("failed to record click")

        return result
