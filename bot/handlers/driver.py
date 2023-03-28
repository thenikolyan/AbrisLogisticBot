from aiogram.types import ParseMode, InlineKeyboardButton
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup


from aiogram.utils.markdown import text, bold
from createBot import bot
from database import db


class Driver(StatesGroup):
    route_number = State()
    pos = State()

    date_route = State()
    number_route = State()
    number_point = State()
    addr_leaving = State()
    time_leaving = State()
    addr_arriving = State()
    time_arriving_fact = State()
    trn = State()
    consignment = State()
    akt = State()
    location = State()


async def menuDriver(callback: types.CallbackQuery):
    try:
        await bot.delete_message(callback.from_user.id, callback.message.message_id)
    except AttributeError:
        pass
    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton(text='Просмотр прикрепленных маршрутов', callback_data='viewAttachedRoutes'),
        types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
    ]

    await bot.send_message(
        callback.from_user.id,
        'Меню управления',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*buttons),
    )
async def viewAttachedRoutes(callback: types.CallbackQuery,state=None):
    routes = await db.getAttachedRoute(callback.from_user.id)
    print(routes)
    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    for line in routes.to_dict('records'):
        buttons.append(types.InlineKeyboardButton(text=f'Маршрут {line["route"]}', callback_data=f'{line["id"]}'))
    buttons.append(types.InlineKeyboardButton(text='Отмена', callback_data='cancel'))
    await bot.send_message(
        callback.from_user.id,
        'Выберете маршрут',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*buttons)
    )
    await Driver.route_number.set()

async def viewChosenRoute(callback: types.CallbackQuery, state:FSMContext):
    routes = await db.getAttachedRoute(callback.from_user.id)
    route = routes.query(f'id == {int(callback.data)}').to_dict('records')
    async with state.proxy() as data:
        data['route_number'] = int(callback.data)
    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton(text='Начать маршрут', callback_data='startRoute'),
        types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
    ]
    await bot.send_message(
        callback.from_user.id,
        f'Ваш маршрут {data["route_number"]}',
        parse_mode=ParseMode.MARKDOWN,

    )
    await bot.send_message(
        callback.from_user.id,
        f'Пункты назначения {route[0]["route"]}',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*buttons)
    )

def register_handlers_clients(dp: Dispatcher):
    dp.register_callback_query_handler(menuDriver, Text(equals='menuDriver', ignore_case=True))
    dp.register_callback_query_handler(viewAttachedRoutes, Text(equals='viewAttachedRoutes', ignore_case=True), state=None)
    dp.register_callback_query_handler(viewChosenRoute, state=Driver.route_number)