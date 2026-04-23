import datetime
import logging

from aiogram import F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, FSInputFile
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Back, SwitchTo, Next, Url, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import Dialog, DialogManager, StartMode, ShowMode
from dialogs.tracked_window import Window

from fsm_forms.fsm_models import Education, MainDialog

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import Click, Session as SessionModel, User
from aiogram.utils.chat_action import ChatActionSender
from config.config import video_for_windows
from lexicon.lexicon import lexicon_ru

education_lexicon: dict[str, list[str]] | dict = lexicon_ru.get('education', {})

LESSON_TITLES: dict[str, str] = {
    'lesson_0': 'Урок 0. Введение. Как устроена электрика в доме',
    'lesson_1': 'Урок 1. Как работает система HiTE PRO',
    'lesson_2': 'Урок 2. Чем HiTE PRO может управлять',
    'lesson_3': 'Урок 3. Как выбрать блок управления',
    'lesson_4': 'Урок 4. Выключатели, пульты и радиомодуль',
    'lesson_5': 'Урок 5. Датчики — что автоматизируют',
    'lesson_6': 'Урок 6. Сервер умного дома — зачем нужен',
    'lesson_7': 'Урок 7. Приложение — что можно делать',
    'lesson_8': 'Урок 8. Сценарии и режимы — настраиваем под себя',
    'lesson_9': 'Урок 9. Собираем всё вместе — типовой проект с нуля',
}

BACK_TO_MENU_TEXT = 'Вернуться к списку уроков'

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
        followup_key = f"{lesson_key}1"
        variants = {
            lesson_key,
            f"Education:{lesson_key}",
            followup_key,
            f"Education:{followup_key}",
        }
        for state_key in (lesson_key, followup_key):
            education_state = getattr(Education, state_key, None)
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

async def _deliver_lesson_video(
    dialog_manager: DialogManager,
    lesson_key: str,
    caption: str | None = None,
) -> None:
    bot: Bot = dialog_manager.middleware_data['bot']
    chat_id = dialog_manager.event.from_user.id
    video_path = video_for_windows.get(lesson_key)
    if video_path is None:
        logger.warning("No video configured for lesson=%s", lesson_key)
        return
    async with ChatActionSender.upload_video(bot=bot, chat_id=chat_id):
        await bot.send_video(
            chat_id=chat_id,
            video=FSInputFile(video_path),
            caption=caption,
        )


async def _start_lesson(
    dialog_manager: DialogManager,
    lesson_key: str,
    followup_state: State,
) -> None:
    lesson_texts = education_lexicon.get(lesson_key) or (None, None)
    main_message = lesson_texts[0] if lesson_texts else None
    await _deliver_lesson_video(dialog_manager, lesson_key, caption=main_message)
    await dialog_manager.switch_to(state=followup_state, show_mode=ShowMode.SEND)


async def lesson_0_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_0', Education.lesson_01)

async def lesson_1_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_1', Education.lesson_11)

async def lesson_2_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_2', Education.lesson_21)

async def lesson_3_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_3', Education.lesson_31)

async def lesson_4_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_4', Education.lesson_41)

async def lesson_5_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_5', Education.lesson_51)

async def lesson_6_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_6', Education.lesson_61)

async def lesson_7_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_7', Education.lesson_71)

async def lesson_8_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_8', Education.lesson_81)

async def lesson_9_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await _start_lesson(dialog_manager, 'lesson_9', Education.lesson_91)

education_menu_window = Window(
    Format(lexicon_ru.get("edu_welcome")),
    Column(
Button(Format("Урок 0 Введение Как устроена электрика в доме"),
               id="0",
               on_click=lesson_0_start,
               ),
        Button(Format("Урок 1. Как работает система HiTE PRO"),
               id="1",
               on_click=lesson_1_start,
               ),
        Button(Format("Урок 2. Чем HiTE PRO может управлять"),
               id="2",
               on_click=lesson_2_start,
               ),
        Button(Format("Урок 3. Как выбрать блок управления"),
               id="3",
               on_click=lesson_3_start,
               ),
        Button(Format("Урок 4. Выключатели, пульты и радиомодуль"),
               id='4',
               on_click=lesson_4_start,
               ),
        Button(Format("Урок 5. Датчики — что автоматизируют"),
               id="5",
               on_click=lesson_5_start,
               ),
        Button(Format("Урок 6. Сервер умного дома — зачем нужен"),
               id="6",
               on_click=lesson_6_start,
               ),
        Button(Format("Урок 7. Приложение — что можно делать"),
               id="7",
               on_click=lesson_7_start,
               ),
        Button(Format("Урок 8. Сценарии и режимы — настраиваем под себя"),
               id="8",
               on_click=lesson_8_start,
               ),
        Button(Format("Урок 9. Собираем всё вместе — типовой проект с нуля"),
               id="9",
               on_click=lesson_9_start,
               ),
        Cancel(Const("Главное меню"))
    ),
    getter=education_menu_getter,
    state=Education.education_menu
)


async def lesson_0_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_0')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_0_window_2 = Window(
    Format("{second_message}"),
    Column(
        Button(Const(LESSON_TITLES['lesson_1']), id='to_next', on_click=lesson_1_start),
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_0_getter,
    state=Education.lesson_01
)

async def lesson_1_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_1')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_1_window_2 = Window(
    Format("{second_message}"),
    Column(
        Button(Const(LESSON_TITLES['lesson_2']), id='to_next', on_click=lesson_2_start),
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_1_getter,
    state=Education.lesson_11
)

async def lesson_2_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_2')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_2_window_2 = Window(
    Format("{second_message}"),
    Column(
        Button(Const(LESSON_TITLES['lesson_3']), id='to_next', on_click=lesson_3_start),
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_2_getter,
    state=Education.lesson_21
)

async def lesson_3_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_3')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_3_window_2 = Window(
    Format("{second_message}"),
    Column(
        Button(Const(LESSON_TITLES['lesson_4']), id='to_next', on_click=lesson_4_start),
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_3_getter,
    state=Education.lesson_31
)


async def lesson_4_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_4')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_4_window_2 = Window(
    Format("{second_message}"),
    Column(
        Button(Const(LESSON_TITLES['lesson_5']), id='to_next', on_click=lesson_5_start),
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_4_getter,
    state=Education.lesson_41
)

async def lesson_5_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_5')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_5_window_2 = Window(
    Format("{second_message}"),
    Column(
        Button(Const(LESSON_TITLES['lesson_6']), id='to_next', on_click=lesson_6_start),
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_5_getter,
    state=Education.lesson_51
)

async def lesson_6_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_6')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_6_window_2 = Window(
    Format("{second_message}"),
    Column(
        Button(Const(LESSON_TITLES['lesson_7']), id='to_next', on_click=lesson_7_start),
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_6_getter,
    state=Education.lesson_61
)

async def lesson_7_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_7')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_7_window_2 = Window(
    Format("{second_message}"),
    Column(
        Button(Const(LESSON_TITLES['lesson_8']), id='to_next', on_click=lesson_8_start),
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_7_getter,
    state=Education.lesson_71
)

async def lesson_8_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_8')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_8_window_2 = Window(
    Format("{second_message}"),
    Column(
        Button(Const(LESSON_TITLES['lesson_9']), id='to_next', on_click=lesson_9_start),
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_8_getter,
    state=Education.lesson_81
)

async def lesson_9_getter(dialog_manager: DialogManager, **kwargs):
    main_message, second_message = education_lexicon.get('lesson_9')
    return {
        'main_message': main_message,
        'second_message': second_message,
    }

lesson_9_window_2 = Window(
    Format("{second_message}"),
    Column(
        SwitchTo(Const(BACK_TO_MENU_TEXT), id='to_menu', state=Education.education_menu),
    ),
    getter=lesson_9_getter,
    state=Education.lesson_91
)

education_dialog = Dialog(
    education_menu_window,
    lesson_0_window_2,
    lesson_1_window_2,
    lesson_2_window_2,
    lesson_3_window_2,
    lesson_4_window_2,
    lesson_5_window_2,
    lesson_6_window_2,
    lesson_7_window_2,
    lesson_8_window_2,
    lesson_9_window_2,
)
