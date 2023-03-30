from aiogram.types import ParseMode, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import datetime

from aiogram.utils.markdown import text, bold
from createBot import bot
from database import db


class Driver(StatesGroup):
    route = State()
    route_number = State()
    pos = State()
    time_leaving = State()
    time_arriving = State()
    address_leaving = State()
    address_arriving = State()
    location_leaving = State()
    location_arriving = State()
    distance = State()
    AKT = State()
    TRN = State()
    consignment = State()



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
        data['route'] = route[0]["route"].split('~')
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

    await Driver.pos.set()


async def followtRoute(callback: types.CallbackQuery, state:FSMContext):

    if callback.data == 'startRoute':
        async with state.proxy() as data:

            data['pos'] = 1
    elif callback.data == 'continueRoute':
        async with state.proxy() as data:
            data['pos'] += 1


    data = await state.get_data()
    print(data)
    if data.get('pos') >= len(data.get('route')):
        await state.finish()
        await bot.send_message(
            callback.from_user.id,
            'Поздравляем, вы завершили маршрут',
            parse_mode=ParseMode.MARKDOWN,

        )
        print('зашел')
        await menuDriver(callback)
    else:

        buttons = [
            types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ]
        inkb = types.InlineKeyboardMarkup(row_width=1)

        await bot.send_message(
            callback.from_user.id,
            'Вам необходимо отправить геолокацию',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=inkb.add(*buttons)
        )
        await Driver.location_leaving.set()

async def getLeavingLocation(message: types.Message, state: FSMContext):
    if message.content_type != 'location':
        await bot.send_message(
            message.from_user.id,
             'Вы похоже ошиблись\n Отправьте геолокацию еще раз',
            parse_mode=ParseMode.MARKDOWN,

        )
        await Driver.location_leaving.set()
    else:
        async with state.proxy() as data:
            data['location_leaving'] = [message.location.latitude, message.location.longitude]


        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton(text='ВЫЕЗД', callback_data='GO'),
            types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ]

        await bot.send_message(
            message.from_user.id,
            f'Ваша следующая точка {data["route"][data["pos"]]}',
            parse_mode=ParseMode.MARKDOWN,

        )
        await bot.send_message(
            message.from_user.id,
            'Когда будете выезжать нажмите кнопку ВЫЕЗД',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=inkb.add(*buttons)
        )
        await Driver.time_leaving.set()
async def getLeavingTimeAddr(callback: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        data['time_leaving'] = datetime.datetime.now()
        data['address_leaving '] = data['route'][data['pos']-1]

    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton(text='ПРИЕХАЛ', callback_data='GO'),
        types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
    ]
    await bot.send_message(
        callback.from_user.id,
        'Когда прибудете нажмите кнопку ПРИЕХАЛ',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*buttons)
    )
    await Driver.time_arriving.set()

async def getArrivingTimeAddr(callback: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        data['time_arriving'] = datetime.datetime.now()
        data['address_arriving '] = data['route'][data['pos']]

    buttons = [
        types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
    ]
    inkb = types.InlineKeyboardMarkup(row_width=1)

    await bot.send_message(
        callback.from_user.id,
        'Вам необходимо отправить геолокацию',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*buttons)
    )
    await Driver.location_arriving.set()


async def getArrivingLocation(message: types.Message, state: FSMContext):
    if message.content_type != 'location':
        await bot.send_message(
            message.from_user.id,
             'Вы похоже ошиблись\n Отправьте геолокацию еще раз',
            parse_mode=ParseMode.MARKDOWN,

        )
        await Driver.location_arriving.set()
    else:
        async with state.proxy() as data:
            data['location_arriving'] = [message.location.latitude, message.location.longitude]
        await db.insertOneRide(dict(data))
        buttons = [
            types.InlineKeyboardButton(text='Перейти к следующей точке', callback_data='continueRoute'),
            types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ]
        inkb = types.InlineKeyboardMarkup(row_width=1)

        await bot.send_message(
            message.from_user.id,
            'Нажмите "Перейти к следующей точке"',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=inkb.add(*buttons)
        )
    await Driver.pos.set()


def register_handlers_clients(dp: Dispatcher):
    dp.register_callback_query_handler(menuDriver, Text(equals='menuDriver', ignore_case=True))
    dp.register_callback_query_handler(viewAttachedRoutes, Text(equals='viewAttachedRoutes', ignore_case=True), state=None)
    dp.register_callback_query_handler(viewChosenRoute, state=Driver.route_number)

    dp.register_callback_query_handler(followtRoute, state=Driver.pos)

    dp.register_message_handler(getLeavingLocation, content_types=['any'],  state=Driver.location_leaving)
    dp.register_callback_query_handler(getLeavingTimeAddr, state=Driver.time_leaving)
    dp.register_callback_query_handler(getArrivingTimeAddr, state=Driver.time_arriving)
    dp.register_message_handler(getArrivingLocation, content_types=['any'], state=Driver.location_arriving)