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

from fsm_forms.fsm_models import MainDialog, Lighting, Curtains, Climate, Leak, Gates, Safety, Saving, Scenarios, \
    Control, Solutions, Contacting, Podbor

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import User
from aiogram.utils.chat_action import ChatActionSender
from config.config import matching_entry_points, video_for_windows
from lexicon.lexicon import lexicon_ru, urls

logger = logging.getLogger(__name__)


async def lighting_1_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('lighting_1')
    message = lexicon_ru.get('lighting_1')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': False,
        'dont_last': True
    }

async def lighting_2_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('lighting_2')
    message = lexicon_ru.get('lighting_2')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def lighting_3_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('lighting_3')
    message = lexicon_ru.get('lighting_3')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def lighting_4_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('lighting_4')
    message = lexicon_ru.get('lighting_4')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def lighting_5_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('lighting_5')
    message = lexicon_ru.get('lighting_5')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def lighting_6_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('lighting_6')
    message = lexicon_ru.get('lighting_6')
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

lighting_1_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=lighting_1_getter,
    state=Lighting.stage_1
)

lighting_2_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=lighting_2_getter,
    state=Lighting.stage_2
)

lighting_3_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=lighting_3_getter,
    state=Lighting.stage_3
)

lighting_4_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=lighting_4_getter,
    state=Lighting.stage_4
)

lighting_5_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=lighting_5_getter,
    state=Lighting.stage_5
)

lighting_6_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=lighting_6_getter,
    state=Lighting.stage_6
)

lighting_dialog = Dialog(lighting_1_window, lighting_2_window, lighting_3_window, lighting_4_window,
                         lighting_5_window, lighting_6_window)
