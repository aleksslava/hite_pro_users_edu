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
from fsm_forms.fsm_models import MainDialog, Solutions, Education, Admin, Examples, Podbor

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import User
from aiogram.utils.chat_action import ChatActionSender
from config.config import matching_entry_points, video_for_windows, pdf_for_windows
from lexicon.lexicon import lexicon_ru, urls

logger = logging.getLogger(__name__)



examples_menu_window = Window(
    Const('Посмотрите типовые проекты умного дома — с планировкой, составом оборудования, ценами и списком решаемых задач. '
          'Выберите тот, который подходит вам больше всего:'),
    Column(
        SwitchTo(Const('1-комнатная — до ремонта'), id='one_room_before', state=Examples.one_room_before),
        SwitchTo(Const('1-комнатная — после ремонта'), id='one_room_after', state=Examples.one_room_after),
        SwitchTo(Const('2-комнатная — до ремонта'), id='two_room_before', state=Examples.two_room_before),
        SwitchTo(Const('2-комнатная — после ремонта'), id='two_room_after', state=Examples.two_room_after),
        SwitchTo(Const('частный дом – до ремонта'), id='house_before', state=Examples.house_before),
        SwitchTo(Const('частный дом — после ремонта'), id='house_after', state=Examples.house_after),
        Start(Const('Главное меню'), id='to_main', state=MainDialog.main_menu),
    ),
    state=Examples.menu,
)


async def one_room_before_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('examples').get('one_room_before')
    return {'message': message, 'pdf_path': pdf_for_windows.get('one_room_before')}


async def one_room_after_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('examples').get('one_room_after')
    return {'message': message, 'pdf_path': pdf_for_windows.get('one_room_after')}


async def two_room_before_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('examples').get('two_room_before')
    return {'message': message, 'pdf_path': pdf_for_windows.get('two_room_before')}


async def two_room_after_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('examples').get('two_room_after')
    return {'message': message, 'pdf_path': pdf_for_windows.get('two_room_after')}


async def house_before_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('examples').get('house_before')
    return {'message': message, 'pdf_path': pdf_for_windows.get('house_before')}


async def house_after_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('examples').get('house_after')
    return {'message': message, 'pdf_path': pdf_for_windows.get('house_after')}

async def call_manager_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('call_manager')
    url = urls.get('roz_manager')
    return {'message': message, 'url': url}


buttons = Column(
    Start(Const('Подобрать под мою квартиру'), id='podbor', state=Podbor.house_type),
    SwitchTo(Const('Другой проект'), id='another_example', state=Examples.menu),
    Start(Const('Связаться'), id='call', state=Examples.call_manager),
)

one_room_before_window = Window(
    Format("{message}"),
    StaticMedia(path=Format("{pdf_path}"), type=ContentType.DOCUMENT),
    buttons,
    getter=one_room_before_getter,
    state=Examples.one_room_before,
)

one_room_after_window = Window(
    Format("{message}"),
    StaticMedia(path=Format("{pdf_path}"), type=ContentType.DOCUMENT),
    buttons,
    getter=one_room_after_getter,
    state=Examples.one_room_after,
)

two_room_before_window = Window(
    Format("{message}"),
    StaticMedia(path=Format("{pdf_path}"), type=ContentType.DOCUMENT),
    buttons,
    getter=two_room_before_getter,
    state=Examples.two_room_before,
)

two_room_after_window = Window(
    Format("{message}"),
    StaticMedia(path=Format("{pdf_path}"), type=ContentType.DOCUMENT),
    buttons,
    getter=two_room_after_getter,
    state=Examples.two_room_after,
)

house_before_window = Window(
    Format("{message}"),
    StaticMedia(path=Format("{pdf_path}"), type=ContentType.DOCUMENT),
    buttons,
    getter=house_before_getter,
    state=Examples.house_before,
)

house_after_window = Window(
    Format("{message}"),
    StaticMedia(path=Format("{pdf_path}"), type=ContentType.DOCUMENT),
    buttons,
    getter=house_after_getter,
    state=Examples.house_after,
)

call_manager = Window(
    Format("{message}"),
    Url(Const("Перейти в чат"), url=Format("{url}")),
    getter=call_manager_getter,
    state=Examples.call_manager,
)


examples_dialog = Dialog(
    examples_menu_window,
    one_room_before_window,
    one_room_after_window,
    two_room_before_window,
    two_room_after_window,
    house_before_window,
    house_after_window,
    call_manager
)

