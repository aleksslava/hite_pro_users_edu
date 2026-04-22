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


async def gates_1_getter(dialog_manager: DialogManager, **kwargs):
    video_path = video_for_windows.get('gates_1')
    message = lexicon_ru.get('gates_1')
    return {
        'video_path': video_path,
        'message': message,
        'dont_first': False,
        'dont_last': True
    }

buttons = Column(
    SwitchTo(Const('Хочу также'), id='want_bue', state=Contacting.get_phone),
    Cancel(Const('Другие темы'), id='to_solutions', show_mode=ShowMode.EDIT),
)

gates_1_window = Window(
Format("{message}"),
    StaticMedia(
            path=Format("{video_path}"),
            type=ContentType.VIDEO,
    ),
    buttons,
    getter=gates_1_getter,
    state=Gates.stage_1
)

gates_dialog = Dialog(gates_1_window)
