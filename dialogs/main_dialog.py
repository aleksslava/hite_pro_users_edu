import datetime
import logging

from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Back, SwitchTo, Next, Url
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode

from fsm_forms.fsm_models import MainDialog, Solutions

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import User
from aiogram.utils.chat_action import ChatActionSender
from config.config import matching_entry_points, video_for_windows
from lexicon.lexicon import lexicon_ru, urls

logger = logging.getLogger(__name__)

async def solutions(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Solutions.menu)

async def education(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    pass

async def examples(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    pass

async def contact(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    pass

main_menu_buttons: Column = Column(
    Button(Const('🔍 Решения'), id='solutions',
                 on_click=solutions),
    Button(Const('📚 Обучение'), id='education',
                 on_click=education),
    Button(Const('🏠 Примеры проектов'), id='examples',
                 on_click=examples),
    Button(Const('💬 Связаться с нами'), id='contact',
                 on_click=contact),
    )

main_menu_window: Window = Window(Const('Главное меню:'), main_menu_buttons, state=MainDialog.main_menu)

async def welcome_getter(dialog_manager: DialogManager, **kwargs):
    if dialog_manager.start_data is not None:
        start_param = dialog_manager.start_data.get("start_param", 'start')
    else:
        start_param = 'start'

    video_path = matching_entry_points.get(start_param)
    message = lexicon_ru.get('welcome_message')
    return {
        'video_path': video_path,
        'message': message,
    }


welcome_window = Window(
    Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    Next(Const('Вперед'), id='next', show_mode=ShowMode.EDIT),
    getter=welcome_getter,
    state=MainDialog.welcome
)


async def who_are_you_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('who_are_you')


async def intresting(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(MainDialog.intresting)

async def planing(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(MainDialog.planing)

async def repair_compleat(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(MainDialog.repair_compleat)

async def electrik(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(MainDialog.electrik)

who_are_you = Window(
    Format("{message}"),
    Column(
    Button(Const("Просто интересно — изучаю тему умного дома"),
                   id="1",
                   on_click=intresting,
                   ),
    Button(Const("Планирую ремонт или сейчас в процессе"),
                   id="2",
                   on_click=planing,
                   ),
    Button(Const("Ремонт уже сделан, хочу что-то улучшить"),
                   id="3",
                   on_click=repair_compleat,
                   ),
    Button(Const("Я электрик или дизайнер — делаю для клиентов"),
                   id="4",
                   on_click=electrik,
                   ),
    ),
    getter=who_are_you_getter,
    state=MainDialog.who_are_you
)

async def intresting_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('intresting_message')
    video_path = video_for_windows.get('video_1')

    return {
        'message': message,
        'video_path': video_path
    }

intresting_window = Window(
    Format("{message}"),
    StaticMedia(
                path="{video_path}",
                type=ContentType.VIDEO,
        ),
    main_menu_buttons,
    getter=intresting_getter,
    state=MainDialog.intresting
)


async def planing_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('planing_message')
    video_path = video_for_windows.get('video_2')

    return {
        'message': message,
        'video_path': video_path
    }


planing_window = Window(
    Format("{message}"),
    StaticMedia(
        path="{video_path}",
        type=ContentType.VIDEO,
    ),
    main_menu_buttons,
    getter=planing_getter,
    state=MainDialog.planing
)

async def repair_compleat_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('repair_compleat')
    video_path = video_for_windows.get('video_3')

    return {
        'message': message,
        'video_path': video_path
    }


repair_compleat_window = Window(
    Format("{message}"),
    StaticMedia(
        path="{video_path}",
        type=ContentType.VIDEO,
    ),
    main_menu_buttons,
    getter=repair_compleat,
    state=MainDialog.repair_compleat
)

async def electrik_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('electrik')
    video_path = video_for_windows.get('video_4')
    partners_bot_edu_tg = urls.get('partners_bot_edu_tg')

    return {
        'message': message,
        'video_path': video_path,
        'partners_bot_edu_tg': partners_bot_edu_tg
    }


electrik_window = Window(
    Format("{message}"),
    StaticMedia(
        path="{video_path}",
        type=ContentType.VIDEO,
    ),
    Url(Const('Стать партнёром HiTE PRO'), url=Format("{partners_bot_edu_tg}"), when='passed'),
    getter=electrik,
    state=MainDialog.electrik
)

main_dialog = Dialog(main_menu_window, welcome_window, who_are_you, intresting_window, planing_window,
                     repair_compleat_window, electrik_window)