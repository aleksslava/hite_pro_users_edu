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

from fsm_forms.fsm_models import MainDialog, Lighting, Curtains, Climate, Leak, Gates, Safety, Saving, Scenarios, \
    Control, Solutions, Contacting

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import User
from aiogram.utils.chat_action import ChatActionSender
from config.config import matching_entry_points, video_for_windows
from lexicon.lexicon import lexicon_ru, urls

logger = logging.getLogger(__name__)


async def climate_1_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('climate_1')
    message = lexicon_ru.get('climate_1')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': False,
        'dont_last': True
    }

async def climate_2_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('climate_2')
    message = lexicon_ru.get('climate_2')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def climate_3_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('climate_3')
    message = lexicon_ru.get('climate_3')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def climate_4_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('climate_4')
    message = lexicon_ru.get('climate_4')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def climate_5_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('climate_5')
    message = lexicon_ru.get('climate_5')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def climate_6_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('climate_6')
    message = lexicon_ru.get('climate_6')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': False
    }

buttons = Column(
    Back(Const('Назад'), id='back', when='dont_first'),
    Next(Const('Далее'), id='next', when='dont_last'),
    SwitchTo(Const('Хочу также'), id='want_bue', state=Contacting.get_phone),
    SwitchTo(Const('Другие темы'), id='to_solutions', state=Solutions.menu),
)

climate_1_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=climate_1_getter,
    state=Climate.stage_1
)

climate_2_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=climate_2_getter,
    state=Climate.stage_2
)

climate_3_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=climate_3_getter,
    state=Climate.stage_3
)

climate_4_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=climate_4_getter,
    state=Climate.stage_4
)

climate_5_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=climate_5_getter,
    state=Climate.stage_5
)

climate_6_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=climate_6_getter,
    state=Climate.stage_6
)