import datetime
import logging

from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Back, SwitchTo, Next, Url, Cancel
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


async def saving_1_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('saving_1')
    message = lexicon_ru.get('saving_1')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': False,
        'dont_last': True
    }

async def saving_2_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('saving_2')
    message = lexicon_ru.get('saving_2')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': True,
        'dont_last': True
    }

async def saving_3_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('saving_3')
    message = lexicon_ru.get('saving_3')
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
    Cancel(Const('Другие темы'), id='to_solutions', show_mode=ShowMode.EDIT),
)

saving_1_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=saving_1_getter,
    state=Saving.stage_1
)

saving_2_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=saving_2_getter,
    state=Saving.stage_2
)

saving_3_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=saving_3_getter,
    state=Saving.stage_3
)

saving_dialog = Dialog(saving_1_window, saving_2_window, saving_3_window)
