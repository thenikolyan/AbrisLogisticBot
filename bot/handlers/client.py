from aiogram.types import ParseMode, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from auxiliary.funcs import cycle
import datetime as dt

from createBot import bot
from database import db


class Route(StatesGroup):
    route = State()
    position = State()

    df = State()
    location = State()
    end = State()



async def getRoute(callback: types.CallbackQuery, state=None):
    await state.finish()
    await Route.df.set()
    routes = await db.getAttachedRoute(callback.from_user.id)

    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    for line in routes.to_dict('records'):
        buttons.append(types.InlineKeyboardButton(text=f'Маршрут: {line["route"]}', callback_data=f'{line["id"]}'))
    buttons.append(types.InlineKeyboardButton(text='Отмена', callback_data='cancel'))

    await bot.send_message(
        callback.from_user.id,
        'Пожалуйста, выберите маршрут, по которому поедете.',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*buttons)
    )


async def viewRoute(callback: types.CallbackQuery, state: FSMContext):
    
    routes = await db.getAttachedRoute(callback.from_user.id)
    route = routes.query(f'id == {int(callback.data)}').to_dict('records')[0]

    admins = await db.getAdmins()
    admins = list(admins['id'])

    driver = await db.getDrivers()
    driver = driver.query(f'id == {int(callback.from_user.id)}').to_dict('records')[0]

    async with state.proxy() as data:
        data['df'] = {'id_user': callback.from_user.id, 
                      'surname': driver['surname'],
                      'name': driver['name'],
                      'patronymic': driver['patronymic'], 
                      'id_route': route['id']}
        data['route'] = cycle(route["route"].split('~'))
        data['position'] = 1

        route = data['route'].to_list
        message_text = f'''Ваш маршрут №{data['df']['id_route']}. 
        Ваши пункты назначения: \n{route}.'''
        message_text_for_admin = f'''Водитель: {data['df']['surname']} {data['df']['name']} {data['df']['patronymic']}, начал поездку по маршруту №{data['df']['id_route']} ({route[0]} -> {route[-1]})'''


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Выехал.', request_location=True),
        types.KeyboardButton(text='Отмена')
    ]


    await bot.send_message(
        chat_id=callback.from_user.id,
        text = message_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*buttons)
    )

    for user in admins:
        await bot.send_message(
        chat_id=user,
        text = message_text_for_admin,
        parse_mode=ParseMode.HTML
        )

    await Route.next()


async def startRoute(message: types.Message, state: FSMContext):
    
    async with state.proxy() as data:
        data['df']['time_leaving'] = dt.datetime.now().replace(microsecond=0)
        data['df']['latitude_leaving'] = message.location.latitude
        data['df']['longitude_leaving'] = message.location.longitude
        data['df']['address_leaving'] = next(data['route'])
        data['df']['address_arriving'] = next(data['route'])

        message_text = f'''Вы выехали из: \n{data['df']['address_leaving']}. 
        \nТочка прибытия: \n{data['df']['address_arriving']}. 
        \nПожалуйста, не забудьте <b>отметиться</b> при приезде.'''


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Приехал.', request_location=True),
        types.KeyboardButton(text='Отмена')
    ]


    await bot.send_message(
        chat_id=message.from_user.id,
        text = message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons)
    )

    await Route.next()


async def nextPoint(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['df']['time_arriving'] = dt.datetime.now().replace(microsecond=0)
        data['df']['latitude_arriving'] = message.location.latitude
        data['df']['longitude_arriving'] = message.location.longitude
    


def register_handlers_clients(dp: Dispatcher):
    dp.register_callback_query_handler(getRoute, Text(equals='getRoute', ignore_case=True), state=None)
    dp.register_callback_query_handler(viewRoute, state=Route.df)
    dp.register_message_handler(startRoute, content_types=['location'], state=Route.location)
    dp.register_message_handler(nextPoint, content_types=['text'], state=Route.end)

    # dp.register_callback_query_handler(viewAttachedRoutes, Text(equals='viewAttachedRoutes', ignore_case=True), state=None)
    # dp.register_callback_query_handler(viewChosenRoute, state=Driver.route_number)

    # dp.register_callback_query_handler(followtRoute, state=Driver.pos)

    # dp.register_message_handler(getLeavingLocation, content_types=['any'],  state=Driver.location_leaving)
    # dp.register_callback_query_handler(getLeavingTimeAddr, state=Driver.time_leaving)
    # dp.register_callback_query_handler(getArrivingTimeAddr, state=Driver.time_arriving)
    # dp.register_message_handler(getArrivingLocation, content_types=['any'], state=Driver.location_arriving)