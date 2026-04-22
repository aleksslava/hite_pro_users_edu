import datetime
import logging
from operator import itemgetter

from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Back, SwitchTo, Next, Url, Start, Multiselect, RequestContact
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory
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

HOUSE_TYPE_LABELS = {
    'room': 'Квартира',
    'house': 'Частный дом или дача',
    'ofice': 'Офис / производство',
    'another': 'Другое',
}


async def house_type_processing(callback_query: CallbackQuery, button: Button, dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data['house_type'] = HOUSE_TYPE_LABELS[button.widget_id]
    await dialog_manager.next()

async def house_type_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('podbor').get('house_type')
    return {'message': message}


house_type = Window(
    Format(text='{message}'),
    Column(
        Button(Const('Квартира'), id='room', on_click=house_type_processing),
        Button(Const('Частный дом или дача'), id='house', on_click=house_type_processing),
        Button(Const('Офис / производство'), id='ofice', on_click=house_type_processing),
        Button(Const('Другое'), id='another', on_click=house_type_processing),
    ),
    getter=house_type_getter,
    state=Podbor.house_type
)


REPAIR_STAGE_LABELS = {
    'repair_in_process': 'Ремонт в процессе',
    'repair_compleat': 'Ремонт уже завершён',
    'repair_planing': 'Пока только планирую',
}


async def repair_stage_processing(callback_query: CallbackQuery, button: Button, dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data['repair_stage'] = REPAIR_STAGE_LABELS[button.widget_id]
    await dialog_manager.next()

async def repair_stage_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('podbor').get('repair_stage')
    return {'message': message}

repair_stage = Window(
    Format(text='{message}'),
    Column(
            Button(Const('Ремонт в процессе'), id='repair_in_process', on_click=repair_stage_processing),
            Button(Const('Ремонт уже завершён'), id='repair_compleat', on_click=repair_stage_processing),
            Button(Const('Пока только планирую'), id='repair_planing', on_click=repair_stage_processing),
        ),
    getter=repair_stage_getter,
    state=Podbor.repair_stage
)

INTERESTS = [
    ('Умный свет', 'light'),
    ('Климат и отопление', 'climate'),
    ('Умные шторы', 'curtains'),
    ('Защита от протечек', 'leak'),
    ('Безопасность', 'safety'),
    ('Сценарии и автоматика', 'scenarios'),
    ('Всё сразу', 'all'),
]


async def intresting_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('podbor').get('interes')
    return {'message': message, 'interests': INTERESTS}


async def on_interest_click(callback: CallbackQuery, select, dialog_manager: DialogManager, item_id: str):
    if item_id == 'all' and select.is_checked('all'):
        for _label, key in INTERESTS:
            if key != 'all':
                await select.set_checked(key, True)


intresting = Window(
    Format(text='{message}'),
    Column(
        Multiselect(
            checked_text=Format('✅ {item[0]}'),
            unchecked_text=Format('◻️ {item[0]}'),
            id='interests_select',
            item_id_getter=itemgetter(1),
            items='interests',
            on_click=on_interest_click,
        ),
        Next(Const('Далее'), id='next'),
    ),
    getter=intresting_getter,
    state=Podbor.interes
)


async def get_phone_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('podbor').get('get_phone')
    return {'message': message}


async def on_contact_received(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    contact = message.contact
    if contact is None:
        return

    checked_ids = set(dialog_manager.find('interests_select').get_checked())
    interests_text = ', '.join(label for label, key in INTERESTS if key in checked_ids)

    answers = {
        'house_type': dialog_manager.dialog_data.get('house_type', ''),
        'repair_stage': dialog_manager.dialog_data.get('repair_stage', ''),
        'intresting': interests_text,
    }

    dialog_manager.dialog_data['phone_number'] = contact.phone_number
    dialog_manager.dialog_data['answers'] = answers
    logger.info('Podbor answers: %s, phone=%s', answers, contact.phone_number)
    await dialog_manager.next()


get_phone_window = Window(
    Format('{message}'),
    RequestContact(Const('Отправить номер телефона')),
    MessageInput(on_contact_received, content_types=ContentType.CONTACT),
    markup_factory=ReplyKeyboardFactory(resize_keyboard=True, one_time_keyboard=True),
    getter=get_phone_getter,
    state=Podbor.get_phone,
)


async def phone_received_getter(dialog_manager: DialogManager, **kwargs):
    message = lexicon_ru.get('podbor').get('phone_received')
    return {'message': message}


phone_received_window = Window(
    Format('{message}'),
    Start(Const('Главное меню'), id='to_main', state=MainDialog.main_menu),
    getter=phone_received_getter,
    state=Podbor.phone_received,
)

podbor_window = Dialog(
    house_type,
    repair_stage,
    intresting,
    get_phone_window,
    phone_received_window
)