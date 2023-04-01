from aiogram.types import ParseMode, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from auxiliary.funcs import cycle
import datetime as dt

from createBot import bot
from database import db

import os
from dotenv import load_dotenv
from pathlib import Path

class Route(StatesGroup):
    admins = State()
    route = State()
    position = State()

    df = State()
    location = State()
    arriving = State()
    act = State()
    trn = State()
    consignment = State()




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
        data['admins'] = admins
        data['df'] = {'id_user': callback.from_user.id, 
                      'surname': driver['surname'],
                      'name': driver['name'],
                      'patronymic': driver['patronymic'], 
                      'id_route': route['id']}
        data['route'] = cycle(route["route"].split('~'))
        data['position'] = 0

        route = data['route'].to_list
        route = '\n'.join(route)
        print(route)
        message_text = f'''Ваш маршрут №{data['df']['id_route']}.\nВаши пункты назначения:\n{route}.'''
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
        data['position'] += 1
        data['df']['time_leaving'] = dt.datetime.now().replace(microsecond=0)
        data['df']['latitude_leaving'] = message.location.latitude
        data['df']['longitude_leaving'] = message.location.longitude
        data['df']['address_leaving'] = next(data['route'])
        data['df']['address_arriving'] = next(data['route'])

        message_text = f'''Вы выехали из: \n{data['df']['address_leaving']}. 
        \nТочка прибытия: \n{data['df']['address_arriving']}. 
        \nПожалуйста, не забудьте <b>отметиться</b> при приезде.'''
        pos = data['position']
        length = len(data['route'].to_list)
        admins = data['admins']
        route = data['route'].to_list
        message_text_for_admin = f'''Водитель: {data['df']['surname']} {data['df']['name']} {data['df']['patronymic']}, закончил поездку по маршруту №{data['df']['id_route']} ({route[0]} -> {route[-1]})'''
    print(pos, length)
    if pos >= length:
        #передать данные в базу на доработке у Ленчика
        await state.finish()
        await bot.send_message(
            chat_id=message.from_user.id,
            text='Поздравляем, вы завершили маршрут!',
            parse_mode=ParseMode.HTML,

        )


        for user in admins:
            await bot.send_message(
                chat_id=user,
                text=message_text_for_admin,
                parse_mode=ParseMode.HTML
            )
    else:
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


async def getArriving(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['df']['time_arriving'] = dt.datetime.now().replace(microsecond=0)
        data['df']['latitude_arriving'] = message.location.latitude
        data['df']['longitude_arriving'] = message.location.longitude
        data['df']['destination'] = 42
        data['route'].previous()

        
        arriving_point = data['df']['address_arriving']
        admins = data['admins']
        message_text = f'''Вы прибыли на точку: {arriving_point}. \nОтправьте фото акта'''
        message_text_for_admin = f'''Водитель: {data['df']['surname']} {data['df']['name']} {data['df']['patronymic']}, прибыл на точку {arriving_point}'''


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Нет акта'),
        types.KeyboardButton(text='Отмена')
    ]

    await bot.send_message(
        chat_id=message.from_user.id,
        text = message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons)
    )

    #strong
    for user in admins:
        await bot.send_message(
        chat_id=user,
        text = message_text_for_admin,
        parse_mode=ParseMode.HTML
        )

    await Route.act.set()

async def getAct(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        async with state.proxy() as data:

            data['df']['act'] = 'no photo'

    else:

        async with state.proxy() as data:
            fio = data['df']['surname'] + ' ' + data['df']['name']
            path = os.getenv('path_', 'default')
            name = rf'\{path}\{fio}\acts\act_{str(message.from_user.id)}_{dt.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.jpg'
            await message.photo[-1].download(name)
            data['df']['act'] = name


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Нет ТРН'),
        types.KeyboardButton(text='Отмена')
    ]

    message_text = f'''Спасибо!. \nОтправьте фото ТРН'''
    await bot.send_message(
        chat_id=message.from_user.id,
        text=message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons)
    )


    await Route.trn.set()


async def getTrn(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        async with state.proxy() as data:

            data['df']['trn'] = 'no photo'

    else:

        async with state.proxy() as data:
            fio = data['df']['surname'] + ' ' + data['df']['name']
            path = os.getenv('path_', 'default')
            name = rf'\{path}\{fio}\trns\trn_{str(message.from_user.id)}_{dt.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.jpg'
            await message.photo[-1].download(name)
            data['df']['trn'] = name


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Нет накладной'),
        types.KeyboardButton(text='Отмена')
    ]

    message_text = f'''Спасибо!. \nОтправьте фото накладной'''
    await bot.send_message(
        chat_id=message.from_user.id,
        text=message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons)
    )


    await Route.consignment.set()

async def getConsignment(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        async with state.proxy() as data:
            data['df']['consignment'] = 'no photo'
    else:

        async with state.proxy() as data:
            fio = data['df']['surname'] + ' ' + data['df']['name']
            path = os.getenv('path_', 'default')
            name = rf'\{path}\{fio}\consignments\consignment_{str(message.from_user.id)}_{dt.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.jpg'
            await message.photo[-1].download(name)
            data['df']['consignment'] = name


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Выезд', request_location=True),
        types.KeyboardButton(text='Отмена')
    ]

    message_text = f'''Как будете выезжать нажмите кнопку выезд'''
    await bot.send_message(
        chat_id=message.from_user.id,
        text=message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons)
    )


    await Route.location.set()
    await startRoute(message)

def register_handlers_clients(dp: Dispatcher):
    dp.register_callback_query_handler(getRoute, Text(equals='getRoute', ignore_case=True), state=None)
    dp.register_callback_query_handler(viewRoute, state=Route.df)
    dp.register_message_handler(startRoute, content_types=['location'], state=Route.location)
    dp.register_message_handler(getArriving, content_types=['location'], state=Route.arriving)
    dp.register_message_handler(getAct, content_types=['photo', 'text'], state=Route.act)
    dp.register_message_handler(getTrn, content_types=['photo', 'text'], state=Route.trn)
    dp.register_message_handler(getConsignment, content_types=['photo', 'text'], state=Route.consignment)
