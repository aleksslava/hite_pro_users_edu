import datetime
import logging

from aiogram import F, Bot
from aiogram.enums import ContentType, ParseMode
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Back, SwitchTo, Next, Url
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode

from fsm_forms.fsm_models import Education, MainDialog

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import Click, Session as SessionModel, User
from aiogram.utils.chat_action import ChatActionSender
from config.config import matching_entry_points, video_for_windows
from lexicon.lexicon import lexicon_ru

education_lexicon: dict[str, list[str]] = lexicon_ru.get('education')

logger = logging.getLogger(__name__)


def _resolve_event_user_id(dialog_manager: DialogManager) -> int | None:
    event = dialog_manager.event
    from_user = getattr(event, "from_user", None)
    if from_user is not None:
        return from_user.id

    update_obj = getattr(event, "update", None)
    if update_obj is not None:
        callback_query = getattr(update_obj, "callback_query", None)
        if callback_query is not None and callback_query.from_user is not None:
            return callback_query.from_user.id

        message = getattr(update_obj, "message", None)
        if message is not None and message.from_user is not None:
            return message.from_user.id

    middleware_user = dialog_manager.middleware_data.get("event_from_user")
    if middleware_user is not None:
        return getattr(middleware_user, "id", None)

    return None


async def education_menu_getter(dialog_manager: DialogManager, **kwargs):
    lesson_keys = list((education_lexicon or {}).keys())
    lesson_variants: dict[str, set[str]] = {}

    for lesson_key in lesson_keys:
        variants = {lesson_key, f"Education:{lesson_key}"}
        education_state = getattr(Education, lesson_key, None)
        state_value = getattr(education_state, "state", None)
        if state_value:
            variants.add(state_value)
        lesson_variants[lesson_key] = variants

    lessons = {lesson_key: False for lesson_key in lesson_keys}

    session: AsyncSession | None = dialog_manager.middleware_data.get("session")
    tg_user_id = _resolve_event_user_id(dialog_manager)
    if session is None or tg_user_id is None or not lesson_variants:
        return {"lessons": lessons}

    user_id = (
        await session.execute(select(User.id).where(User.tg_user_id == tg_user_id))
    ).scalar_one_or_none()
    if user_id is None:
        return {"lessons": lessons}

    all_lesson_windows = {
        dialog_window
        for variants in lesson_variants.values()
        for dialog_window in variants
    }

    dialog_windows = set(
        (
            await session.execute(
                select(Click.dialog_window)
                .join(SessionModel, SessionModel.id == Click.session_id)
                .where(
                    SessionModel.user_id == user_id,
                    Click.dialog_window.in_(all_lesson_windows),
                )
                .distinct()
            )
        ).scalars().all()
    )

    lessons = {
        lesson_key: bool(dialog_windows.intersection(variants))
        for lesson_key, variants in lesson_variants.items()
    }

    return {"lessons": lessons}

async def lesson_0_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(state=Education.lesson_0, show_mode=ShowMode.EDIT)
    await dialog_manager.switch_to(state=Education.lesson_01, show_mode=ShowMode.SEND)

education_menu_window = Window(
    Format(lexicon_ru.get("edu_welcome")),
    Column(
Button(Format("Урок 0 Введение Как устроена электрика в доме"),
               id="0",
               on_click=lesson_0_start,
               ),
        Button(Format("Урок 1. Как работает система HiTE PRO", when="lesson_1"),
               id="1",
               on_click=lesson_0_start,
               ),
        Button(Format("Урок 2. Чем HiTE PRO может управлять (здесь про функционал блоков управления)"),
               id="2",
               on_click=lesson_0_start,
               when="user_authorized"),
        Button(Format("Урок 3. Как выбрать блок управления (здесь про отличия между компактными и щитовыми блоками)"),
               id="3",
               on_click=lesson_0_start,
               when="user_authorized"),
        Button(Format("Урок 4. Выключатели, пульты и радиомодуль "),
               id='4',
               on_click=lesson_0_start,
               when="user_authorized"),
        Button(Format("Урок 5. Датчики — что автоматизируют"),
               id="5",
               on_click=lesson_0_start,
               when="user_authorized"),
        Button(Format("Урок 6. Сервер умного дома — зачем нужен"),
               id="6",
               on_click=lesson_0_start,
               when="user_authorized"),
        Button(Format("Урок 7. Приложение — что можно делать"),
               id="7",
               on_click=lesson_0_start,
               when="user_authorized"),
        Button(Format("Урок 8. Сценарии и режимы — настраиваем под себя"),
               id="8",
               on_click=lesson_0_start,
               when="user_authorized"),
        Button(Format("Урок 9. Собираем всё вместе — типовой проект с нуля"),
               id="9",
               on_click=lesson_0_start,
               when='button_to_authorized'),
        Button(Format('Главное меню'),
               id='main_menu',
               on_click=lesson_0_start,
               when='is_admin'),
    ),
    getter=education_menu_getter,
    state=Education.education_menu
)


async def education_getter(dialog_manager: DialogManager, **kwargs):
    current_state = dialog_manager.current_context().state.state
    current_lesson = current_state.split(':')[1]
    main_message, second_message = education_lexicon.get(current_lesson)
    video_path = video_for_windows.get('lesson_1')
    return {
        'main_message': main_message,
        'second_message': second_message,
        'video_path': video_path,
    }

lesson_0_window_1 = Window(
    Format("{'main_message'}"),
    StaticMedia(
        path="{video_path}",
        type=ContentType.VIDEO,
    ),
    getter=education_getter,
    state=Education.lesson_0
)

lesson_0_window_2 = Window(
    Format("{'second_message'}"),
    getter=education_getter,
    state=Education.lesson_01
)


education_dialog = Dialog(education_menu_window, lesson_0_window_1, lesson_0_window_2)