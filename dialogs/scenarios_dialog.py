import datetime
import logging

from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Back, SwitchTo, Next, Url, Cancel, Start
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import Dialog, DialogManager, StartMode, ShowMode
from dialogs.tracked_window import Window

from fsm_forms.fsm_models import Scenarios, Solutions, Contacting, Podbor

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import User
from aiogram.utils.chat_action import ChatActionSender
from config.config import matching_entry_points, video_for_windows
from lexicon.lexicon import lexicon_ru, urls

logger = logging.getLogger(__name__)


async def scenarios_1_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('scenarios_1')
    message = lexicon_ru.get('scenarios_1')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': False,
        'dont_last': True
    }

async def scenarios_2_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('scenarios_2')
    message = lexicon_ru.get('scenarios_2')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def scenarios_3_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('scenarios_3')
    message = lexicon_ru.get('scenarios_3')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def scenarios_4_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('scenarios_4')
    message = lexicon_ru.get('scenarios_4')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def scenarios_5_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('scenarios_5')
    message = lexicon_ru.get('scenarios_5')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def scenarios_6_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('scenarios_6')
    message = lexicon_ru.get('scenarios_6')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': False
    }

buttons = Column(
    Back(Const('Назад'), id='back', when='dont_first'),
    Next(Const('Далее'), id='next', when='dont_last'),
    Start(Const('Хочу также'), id='want_bue', state=Podbor.get_phone),
    Cancel(Const('Другие темы'), id='to_solutions', show_mode=ShowMode.EDIT),
)

scenarios_1_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=scenarios_1_getter,
    state=Scenarios.stage_1
)

scenarios_2_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=scenarios_2_getter,
    state=Scenarios.stage_2
)

scenarios_3_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=scenarios_3_getter,
    state=Scenarios.stage_3
)

scenarios_4_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=scenarios_4_getter,
    state=Scenarios.stage_4
)

scenarios_5_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=scenarios_5_getter,
    state=Scenarios.stage_5
)

scenarios_6_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=scenarios_6_getter,
    state=Scenarios.stage_6
)

scenarios_dialog = Dialog(scenarios_1_window, scenarios_2_window, scenarios_3_window, scenarios_4_window,
                          scenarios_5_window, scenarios_6_window)
