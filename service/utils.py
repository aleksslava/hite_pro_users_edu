from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class StartParamType(str, Enum):
    EMPTY = "empty"
    WEBHOOK_ID = "webhook_id"
    TEXT = "text"


@dataclass(frozen=True)
class StartParam:
    kind: StartParamType
    webhook_id: int | None = None
    text: str | None = None


def parse_start_param(raw_start_param: str | None) -> StartParam:
    normalized_param = (raw_start_param or "").strip()

    if not normalized_param:
        return StartParam(kind=StartParamType.EMPTY)

    if normalized_param.isdigit():
        return StartParam(kind=StartParamType.WEBHOOK_ID, webhook_id=int(normalized_param))

    return StartParam(kind=StartParamType.TEXT, text=normalized_param)


def build_empty_utm_data() -> dict[str, str]:
    return {
        "utm_source": "",
        "utm_medium": "",
        "utm_campaign": "",
        "utm_content": "",
        "utm_term": "",
        "yclid": "",
    }


def _normalize_utm_payload(payload: dict[str, Any], base_data: dict[str, str]) -> dict[str, str]:
    normalized_data = base_data.copy()

    for key in normalized_data:
        value = payload.get(key)
        if value is None:
            continue
        normalized_data[key] = str(value)

    return normalized_data


async def fetch_utm_by_webhook_id(
    *,
    webhook_url: str,
    utm_token: str,
    webhook_id: int,
    timeout_seconds: int = 10,
) -> dict[str, str]:
    empty_utm_data = build_empty_utm_data()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{webhook_url}{webhook_id}",
                params={"utm_token": utm_token},
                timeout=timeout_seconds,
            ) as response:
                response.raise_for_status()
                payload = await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        logger.debug("Failed to fetch UTM data for webhook_id=%s", webhook_id, exc_info=True)
        return empty_utm_data

    if not isinstance(payload, dict):
        logger.warning(
            "Unexpected UTM payload type for webhook_id=%s: %s",
            webhook_id,
            type(payload).__name__,
        )
        return empty_utm_data

    utm_data = _normalize_utm_payload(payload, empty_utm_data)
    logger.info(
        "UTM data fetched: source=%s, medium=%s, campaign=%s, content=%s, term=%s, yclid=%s",
        utm_data["utm_source"],
        utm_data["utm_medium"],
        utm_data["utm_campaign"],
        utm_data["utm_content"],
        utm_data["utm_term"],
        utm_data["yclid"],
    )

    return utm_data
