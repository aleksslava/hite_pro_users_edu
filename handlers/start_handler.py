import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from fsm_forms.fsm_models import MainDialog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession



from db import User
from service.utils import (
    StartParamType,
    build_empty_utm_data,
    fetch_utm_by_webhook_id,
    parse_start_param,
)

logger = logging.getLogger(__name__)

main_menu_router = Router()

def _resolve_event_user(dialog_manager: DialogManager):
    event = dialog_manager.event
    from_user = getattr(event, "from_user", None)
    if from_user is not None:
        return from_user

    update = getattr(event, "update", None)
    if update is not None:
        callback_query = getattr(update, "callback_query", None)
        if callback_query is not None and callback_query.from_user is not None:
            return callback_query.from_user

        message = getattr(update, "message", None)
        if message is not None and message.from_user is not None:
            return message.from_user

    return dialog_manager.middleware_data.get("event_from_user")


@main_menu_router.message(Command("start"))
async def start(message: Message, dialog_manager: DialogManager, command: CommandObject):
    webhook_url = dialog_manager.middleware_data["webhook_url"]
    utm_token = dialog_manager.middleware_data["utm_token"]
    session: AsyncSession = dialog_manager.middleware_data['session']

    from_user = _resolve_event_user(dialog_manager)
    if from_user is None:
        raise ValueError("Cannot resolve user from dialog event")
    tg_id = from_user.id
    logger.info(f'Запущен бот пользователем tg_ID:{tg_id}')

    start_param = parse_start_param(command.args if command else None)
    utm_data = build_empty_utm_data()
    dialog_data = {"utm_data": utm_data}

    if start_param.kind == StartParamType.EMPTY:
        logger.info("User started bot without start parameter")
    elif start_param.kind == StartParamType.WEBHOOK_ID:
        logger.info("User started bot with webhook_id: %s", start_param.webhook_id)
        if start_param.webhook_id is not None:
            utm_data = await fetch_utm_by_webhook_id(
                webhook_url=webhook_url,
                utm_token=utm_token,
                webhook_id=start_param.webhook_id,
            )
            dialog_data["utm_data"] = utm_data
    else:
        logger.info("User started bot with text start parameter: %s", start_param.text)
        dialog_data["start_param"] = start_param.text

    result = await session.execute(select(User).where(User.tg_user_id == tg_id))
    user = result.scalar_one_or_none()
    if user is None:
        logger.info(f'Для пользователя tg_id:{tg_id} не найдена запись в БД, создаю новую запись!')

        user = User(
            tg_user_id=tg_id,
            username=from_user.username,
            first_name=from_user.first_name,
            last_name=from_user.last_name,
            utm_campaign=utm_data.get("utm_campaign", ''),
            utm_medium=utm_data.get("utm_medium", ''),
            utm_content=utm_data.get("utm_content", ''),
            utm_term=utm_data.get("utm_term", ''),
            utm_source=utm_data.get("utm_source", ''),
            yclid=utm_data.get("yclid", ''),
            start_parameter=dialog_data.get("start_param", 'start'),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f'Создана новая запись в таблице USERS: tg_id: {user.tg_user_id}, '
                    f' username: {user.username}, '
                    f' first_name: {user.first_name}')

        # Запуск диалога в зависимости от переданного стартового параметра
        await dialog_manager.start(state=MainDialog.welcome,
                                   mode=StartMode.RESET_STACK,
                                   data=dialog_data)

    else:
        logger.info(f'Получена запись user из БД: tg_id: {user.tg_user_id}, '
                    f' username: {user.username}, '
                    f' first_name: {user.first_name}')

        await dialog_manager.start(MainDialog.main_menu, mode=StartMode.RESET_STACK)


@main_menu_router.callback_query(F.data == 'start')
async def start_notification(callback: CallbackQuery, dialog_manager: DialogManager):
    await dialog_manager.start(MainDialog.main_menu, mode=StartMode.RESET_STACK)
