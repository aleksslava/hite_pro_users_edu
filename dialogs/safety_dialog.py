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


async def safety_1_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('safety_1')
    message = lexicon_ru.get('safety_1')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': False,
        'dont_last': True
    }

async def safety_2_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('safety_2')
    message = lexicon_ru.get('safety_2')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def safety_3_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('safety_3')
    message = lexicon_ru.get('safety_3')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def safety_4_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('safety_4')
    message = lexicon_ru.get('safety_4')
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

safety_1_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=safety_1_getter,
    state=Safety.stage_1
)

safety_2_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=safety_2_getter,
    state=Safety.stage_2
)

safety_3_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=safety_3_getter,
    state=Safety.stage_3
)

safety_4_window = Window(
Format("{message}"),
    StaticMedia(
            path="{video_path}",
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=safety_4_getter,
    state=Safety.stage_4
)


safety_dialog = Dialog(safety_1_window, safety_2_window, safety_3_window, safety_4_window)