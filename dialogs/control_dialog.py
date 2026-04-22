import datetime
import logging

from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Back, SwitchTo, Next, Url, Cancel, Start
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import Dialog, Window, DialogManager, ShowMode

from fsm_forms.fsm_models import Control, Solutions, Contacting, Podbor

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import User
from aiogram.utils.chat_action import ChatActionSender
from config.config import matching_entry_points, video_for_windows
from lexicon.lexicon import lexicon_ru, urls

logger = logging.getLogger(__name__)


async def control_1_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('control_1')
    message = lexicon_ru.get('control_1')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': False,
        'dont_last': True
    }

async def control_2_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('control_2')
    message = lexicon_ru.get('control_2')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def control_3_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('control_3')
    message = lexicon_ru.get('control_3')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def control_4_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('control_4')
    message = lexicon_ru.get('control_4')
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

control_1_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=control_1_getter,
    state=Control.stage_1
)

control_2_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=control_2_getter,
    state=Control.stage_2
)

control_3_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=control_3_getter,
    state=Control.stage_3
)

control_4_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=control_4_getter,
    state=Control.stage_4
)


control_dialog = Dialog(control_1_window, control_2_window, control_3_window, control_4_window)

