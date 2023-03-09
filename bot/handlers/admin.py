from aiogram.types import ParseMode, InlineKeyboardButton
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup


from aiogram.utils.markdown import text, bold
from createBot import bot
from database import db


class Role(StatesGroup):
    start = State()
    end = State()


async def controlPanel(callback: types.CallbackQuery):

    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton(text='Просмотр списка водителей', callback_data='diriversList'),
        types.InlineKeyboardButton(text='Сбор отчета', callback_data='createReport'),
        types.InlineKeyboardButton(text='Подтверждение регистрации', callback_data='approveRegistration'),
        types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
    ]

    await bot.send_message(
        callback.from_user.id,
        'Панель управления',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*buttons),
    )


async def approveRegistration(callback: types.CallbackQuery, state=None):
    await state.finish()
    await Role.start.set()

    users = await db.getUnauthorizedUsers()

    await bot.send_message(
        callback.from_user.id,
        users.to_string(index=False) + '\n\nВнесите id пользователя, регистрацию которого необходимо назначить (цифрами) и роль (admin/driver)\n Пример: 123445678 admin',
    )

    await Role.next()


async def setRole(message: types.Message, state: FSMContext):
    id, role = message.text.split(' ')
    if role in ['admin', 'driver']:
        message_text = '0'
        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton(text='Отмена', callback_data='cancel'),
        ]
        await bot.send_message(
            message.from_user.id,
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=inkb.add(*buttons),
        )

        await state.finish()
    else:

        await bot.send_message(
            message.from_user.id,
            'Не верно введена роль.',
            parse_mode=ParseMode.MARKDOWN,
        )
        await approveRegistration(message, state)



def register_handlers_clients(dp: Dispatcher):
    dp.register_callback_query_handler(controlPanel,  Text(equals='controlPanel', ignore_case=True))
    dp.register_callback_query_handler(approveRegistration, Text(equals='approveRegistration', ignore_case=True), state=None)
    dp.register_message_handler(setRole, content_types=['text'], state=Role.end)
