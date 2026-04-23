import datetime
import logging

from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Back, SwitchTo, Next, Url
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import Dialog, DialogManager, StartMode, ShowMode
from dialogs.tracked_window import Window

from fsm_forms.fsm_models import MainDialog, Lighting, Curtains, Climate, Leak, Gates, Safety, Saving, Scenarios, \
    Control, Solutions

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.models import User
from aiogram.utils.chat_action import ChatActionSender
from config.config import matching_entry_points, video_for_windows
from lexicon.lexicon import lexicon_ru, urls

logger = logging.getLogger(__name__)

async def lighting(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Lighting.stage_1)

async def curtains(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Curtains.stage_1)

async def climate(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Climate.stage_1)

async def leak(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Leak.stage_1)

async def gates(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Gates.stage_1)

async def safety(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Safety.stage_1)

async def saving(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Saving.stage_1)

async def scenarios(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Scenarios.stage_1)

async def control(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(Control.stage_1)


async def solutions_getter(dialog_manager: DialogManager, **kwargs):
    return {}


solutions_menu_buttons: Column = Column(
    Button(Const('💡Освещение'), id='lighting',
                 on_click=lighting),
    Button(Const('🪟 Шторы'), id='curtains',
                 on_click=curtains),
    Button(Const('🌡 Климат'), id='climate',
                 on_click=climate),
    Button(Const('💧 Защита от протечек'), id='leak',
                 on_click=leak),
    Button(Const('🚗 Ворота'), id='gates',
                     on_click=gates),
    Button(Const('🔒 Безопасность'), id='safety',
                     on_click=safety),
    Button(Const('📊 Мониторинг и экономия энергии'), id='saving',
                     on_click=saving),
    Button(Const('🎬 Сценарии'), id='scenarios',
                     on_click=scenarios),
    Button(Const('📱 Как управлять'), id='control',
                     on_click=control),
    )

solutions_window = Window(
    Format(lexicon_ru.get('solutions')),
    solutions_menu_buttons,
    getter=solutions_getter,
    state=Solutions.menu,
)

solution_dialog = Dialog(solutions_window)
