from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile
from aiogram_dialog.api.entities import MediaId
from aiogram_dialog.api.protocols import MediaIdStorageProtocol

from config.config import matching_entry_points, video_for_windows

logger = logging.getLogger(__name__)

_cached_video_ids: dict[str, str] = {}
_video_paths_by_key: dict[str, Path] = {}


def get_cached_video_id(video_key: str) -> str | None:
    return _cached_video_ids.get(video_key)


def get_configured_video_path(video_key: str) -> Path | None:
    cached_path = _video_paths_by_key.get(video_key)
    if cached_path is not None:
        return cached_path

    configured_path = video_for_windows.get(video_key) or matching_entry_points.get(video_key)
    if configured_path is None:
        return None
    return Path(configured_path)


def _collect_configured_videos() -> dict[str, Path]:
    videos: dict[str, Path] = {}
    for source in (matching_entry_points, video_for_windows):
        for key, path in source.items():
            if path is None:
                continue
            videos[key] = Path(path)
    return videos


async def warmup_videos_in_telegram(
    *,
    bot: Bot,
    media_id_storage: MediaIdStorageProtocol,
    cache_chat_id: int,
) -> None:
    _cached_video_ids.clear()
    _video_paths_by_key.clear()
    _video_paths_by_key.update(_collect_configured_videos())

    if not _video_paths_by_key:
        logger.info("video warmup skipped: no configured videos")
        return

    keys_by_path: dict[Path, list[str]] = defaultdict(list)
    for key, path in _video_paths_by_key.items():
        keys_by_path[path].append(key)

    logger.info(
        "video warmup started: %d keys, %d unique files",
        len(_video_paths_by_key),
        len(keys_by_path),
    )

    warmed_count = 0
    for path, keys in keys_by_path.items():
        if not path.exists():
            logger.warning("video warmup skipped, file not found: %s (keys=%s)", path, ",".join(keys))
            continue

        try:
            probe_message = await bot.send_video(
                chat_id=cache_chat_id,
                video=FSInputFile(path),
                disable_notification=True,
            )
        except TelegramAPIError:
            logger.exception("video warmup failed for path=%s", path)
            continue

        if probe_message.video is None:
            logger.warning("video warmup response has no video payload: %s", path)
            continue

        media_id = MediaId(
            file_id=probe_message.video.file_id,
            file_unique_id=probe_message.video.file_unique_id,
        )

        await media_id_storage.save_media_id(
            path=str(path),
            url=None,
            type=ContentType.VIDEO,
            media_id=media_id,
        )
        for key in keys:
            _cached_video_ids[key] = media_id.file_id
        warmed_count += 1

        try:
            await bot.delete_message(chat_id=cache_chat_id, message_id=probe_message.message_id)
        except TelegramAPIError:
            logger.debug("video warmup: cannot delete probe message for %s", path)

    logger.info("video warmup finished: %d/%d unique files warmed", warmed_count, len(keys_by_path))
