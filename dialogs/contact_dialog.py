import datetime
import logging

from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Back, SwitchTo, Next, Url, Start
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode

from dialogs.main_dialog import examples
from fsm_forms.fsm_models import MainDialog, Solutions, Education, Admin, Examples, Podbor, Contact

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import User
from aiogram.utils.chat_action import ChatActionSender
from config.config import matching_entry_points, video_for_windows, pdf_for_windows
from lexicon.lexicon import lexicon_ru, urls

logger = logging.getLogger(__name__)

async def our_contact_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('our_contact')
    url = urls.get('roz_manager')
    return {'message': message,
            'url': url,}

our_contacts = Window(
    Format('{message}'),
    Column(
        Url(Const('Написать менеджеру'), url=Format('{url}')),
        Start(Const('Получить расчет'), id='to_podbor', state=Podbor.house_type),
        Url(Const('Позвонить'), url=Const('tel:74952563300'))
    ),
    state=Contact.our_contact,
    getter=our_contact_getter
)

contact_dialog = Dialog(
    our_contacts
)