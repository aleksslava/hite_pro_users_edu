import logging
from datetime import datetime, timezone

from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Column, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from fsm_forms.fsm_models import Admin
from service.analytics_report import build_analytics_xlsx

logger = logging.getLogger(__name__)


async def get_analytics(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    session: AsyncSession = dialog_manager.middleware_data['session']
    await callback.answer('Формирую отчёт...')
    xlsx_bytes = await build_analytics_xlsx(session)
    filename = f"analytics_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.xlsx"
    await callback.message.answer_document(
        BufferedInputFile(xlsx_bytes, filename=filename),
        caption='Аналитика'
    )


def _parse_tg_id(text: str) -> int | None:
    text = text.strip()
    if text.startswith('-'):
        return None
    return int(text) if text.isdigit() else None


async def on_delete_user_input(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    tg_id = _parse_tg_id(message.text or '')
    if tg_id is None:
        dialog_manager.dialog_data['result_message'] = 'Некорректный telegram_id. Введите целое число.'
        await dialog_manager.switch_to(Admin.result)
        return

    session: AsyncSession = dialog_manager.middleware_data['session']
    user = (await session.execute(select(User).where(User.tg_user_id == tg_id))).scalar_one_or_none()
    if user is None:
        dialog_manager.dialog_data['result_message'] = f'Пользователь с tg_id={tg_id} не найден.'
        await dialog_manager.switch_to(Admin.result)
        return

    await session.delete(user)
    await session.commit()
    logger.info('Admin deleted user tg_id=%s', tg_id)
    dialog_manager.dialog_data['result_message'] = f'Пользователь tg_id={tg_id} удалён.'
    await dialog_manager.switch_to(Admin.result)


async def on_add_admin_input(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    tg_id = _parse_tg_id(message.text or '')
    if tg_id is None:
        dialog_manager.dialog_data['result_message'] = 'Некорректный telegram_id. Введите целое число.'
        await dialog_manager.switch_to(Admin.result)
        return

    session: AsyncSession = dialog_manager.middleware_data['session']
    user = (await session.execute(select(User).where(User.tg_user_id == tg_id))).scalar_one_or_none()
    if user is None:
        dialog_manager.dialog_data['result_message'] = f'Пользователь с tg_id={tg_id} не найден.'
        await dialog_manager.switch_to(Admin.result)
        return

    user.is_admin = True
    await session.commit()
    logger.info('Admin granted admin rights to tg_id=%s', tg_id)
    dialog_manager.dialog_data['result_message'] = f'Пользователю tg_id={tg_id} выданы права администратора.'
    await dialog_manager.switch_to(Admin.result)


async def result_getter(dialog_manager: DialogManager, **kwargs):
    return {'result_message': dialog_manager.dialog_data.get('result_message', '')}


admin_menu_window = Window(
    Const('Меню администратора'),
    Column(
        Button(Const('📊 Получить Excel с аналитикой'), id='get_analytics', on_click=get_analytics),
        SwitchTo(Const('🗑 Удалить пользователя'), id='to_delete', state=Admin.delete_user_input),
        SwitchTo(Const('➕ Добавить администратора'), id='to_add_admin', state=Admin.add_admin_input),
        Cancel(Const('◀ Назад в главное меню'), id='to_main'),
    ),
    state=Admin.menu,
)

delete_user_window = Window(
    Const('Введите telegram_id пользователя для удаления:'),
    MessageInput(on_delete_user_input),
    SwitchTo(Const('◀ Назад'), id='back_to_menu', state=Admin.menu),
    state=Admin.delete_user_input,
)

add_admin_window = Window(
    Const('Введите telegram_id пользователя, которому выдать права администратора:'),
    MessageInput(on_add_admin_input),
    SwitchTo(Const('◀ Назад'), id='back_to_menu', state=Admin.menu),
    state=Admin.add_admin_input,
)

result_window = Window(
    Format('{result_message}'),
    SwitchTo(Const('◀ В меню администратора'), id='back_to_menu', state=Admin.menu),
    getter=result_getter,
    state=Admin.result,
)

admin_dialog = Dialog(admin_menu_window, delete_user_window, add_admin_window, result_window)
