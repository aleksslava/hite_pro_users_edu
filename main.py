import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties

from config.config import SessionPolicy, load_config
from db import async_session_factory, init_db, shutdown_db
from dialogs.control_dialog import control_dialog
from dialogs.curtains_dialog import curtains_dialog
from dialogs.education_dialog import education_dialog
from dialogs.gates_dialog import gates_dialog
from dialogs.leak_dialog import leak_dialog
from dialogs.lighting_dialog import lighting_dialog
from dialogs.main_dialog import main_dialog
from dialogs.safety_dialog import safety_dialog
from dialogs.saving_dialog import saving_dialog
from dialogs.scenarios_dialog import scenarios_dialog
from dialogs.solutions_dialog import solution_dialog
from handlers.start_handler import main_menu_router
from middlewares.clicks import ClickTrackingMiddleware
from middlewares.db import DbSessionMiddleware
from service import close_stale_sessions

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')

logger.info("Starting hitepro_users_edu")

config = load_config()
storage = MemoryStorage()

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)
dp.update.middleware(DbSessionMiddleware())
dp.callback_query.outer_middleware(ClickTrackingMiddleware(config.session_policy))

dp.include_router(main_menu_router)
dp.include_routers(main_dialog, solution_dialog, lighting_dialog, curtains_dialog, leak_dialog, gates_dialog,
                   safety_dialog, saving_dialog, scenarios_dialog, control_dialog, education_dialog)
setup_dialogs(dp)

_sweeper_task: asyncio.Task[None] | None = None


async def _run_sweeper(policy: SessionPolicy) -> None:
    interval = policy.sweeper_interval_seconds
    while True:
        try:
            async with async_session_factory() as db:
                closed = await close_stale_sessions(db)
                if closed:
                    await db.commit()
                    logger.info("sweeper closed %d stale sessions", closed)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("sweeper iteration failed")
        await asyncio.sleep(interval)


async def on_startup(bot: Bot, **_: object) -> None:
    global _sweeper_task
    try:
        await init_db()
    except Exception as exc:
        logger.exception("DB init failed: %s", exc)
        return
    _sweeper_task = asyncio.create_task(_run_sweeper(config.session_policy))


async def on_shutdown(bot: Bot, **_: object) -> None:
    global _sweeper_task
    if _sweeper_task is not None:
        _sweeper_task.cancel()
        try:
            await _sweeper_task
        except asyncio.CancelledError:
            pass
        _sweeper_task = None
    await shutdown_db()


dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)


if __name__ == '__main__':
    dp.run_polling(bot)
