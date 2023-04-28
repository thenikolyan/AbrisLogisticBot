import os

from aiogram.types import ParseMode, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from auxiliary.funcs import cycle, distance
from auxiliary.catalog import names
import datetime as dt

from createBot import bot
from database import db


class Route(StatesGroup):
    admins = State()
    route = State()

    df = State()
    location = State()
    arriving = State()
    act = State()
    trn = State()
    consignment = State()
    finish_route = State()


async def getRoute(callback: types.CallbackQuery, state=None):

    await Route.df.set()
    routes = await db.getAttachedRoute(callback.from_user.id)

    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    list_routes = []
    for line in routes.to_dict('records'):
        tmp = line["route"].split('~')
        list_routes.append({'id': line["id"],'route': f'''Начальная точка: <code>{tmp[0]}</code>\nКонечная точка: <code>{tmp[-1]}</code>'''})
        buttons.append(types.InlineKeyboardButton(text=f'Маршрут №{line["id"]}', callback_data=f'{line["id"]}'))
    buttons.append(types.InlineKeyboardButton(text='Отмена', callback_data='cancel'))

    message_text = '''Пожалуйста, выберите маршрут, по которому поедете.\n'''
    for x in list_routes:
        message_text += f'''\n<b>Маршрут №{str(x['id'])}:</b>\n{x['route']}\n'''

    await bot.send_message(
        callback.from_user.id,
        text=message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons)
    )


async def viewRoute(callback: types.CallbackQuery, state: FSMContext):
    
    routes = await db.getAttachedRoute(callback.from_user.id)
    route = routes.query(f'id == {int(callback.data)}').to_dict('records')[0]

    admins = await db.getAdmins()
    admins = list(admins['id'])

    driver = await db.getDrivers()
    driver = driver.query(f'id == {int(callback.from_user.id)}').to_dict('records')[0]

    max_id = await db.getMaxIdRoutes()

    async with state.proxy() as data:
        data['admins'] = admins
        data['df'] = {'id': max_id,
                      'id_user': callback.from_user.id, 
                      'surname': driver['surname'],
                      'name': driver['name'],
                      'patronymic': driver['patronymic'], 
                      'id_route': route['id'],
                      'position': 0}
        data['route'] = cycle(route["route"].split('~'))


        route = '\n'.join(data['route'].to_list)
        message_text = f'''Ваш маршрут №{data['df']['id_route']}.\n\nВаш маршрут:\n{route}.'''
        message_text_for_admin = f'''Водитель: {data['df']['surname']} {data['df']['name']} {data['df']['patronymic']}, начал поездку по маршруту №{data['df']['id_route']} ({route[0]} -> {route[-1]})'''


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Выехал', request_location=True),
        types.KeyboardButton(text='Отмена')
    ]


    await bot.send_message(
        chat_id=callback.from_user.id,
        text = message_text,
        parse_mode=ParseMode.HTML,
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
        data['df']['position'] += 1
        position = data['df']['position']
        length = len(data['route'].to_list)
        data['df']['address_leaving'] = next(data['route'])
        data['df']['address_arriving'] = next(data['route'])

        message_text = f'''Вы выехали из: \n<code>{data['df']['address_leaving']}</code>.\n\nТочка прибытия: \n<code>{data['df']['address_arriving']}</code>.\nПожалуйста, не забудьте <b><u>отметиться</u></b> при приезде. \nНе забудьте завершить поездку!'''


    if position >= length:
        await Route.finish_route.set()

        inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        buttons = [
            types.KeyboardButton(text='Закончить поездку', request_location=True),
            types.KeyboardButton(text='Отмена')
        ]
        
        await bot.send_message(
            chat_id=message.from_user.id,
            text = message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=inkb.add(*buttons)
        )

    else:
        async with state.proxy() as data:
            data['df']['date_leaving'] = dt.datetime.now().date()
            data['df']['time_leaving'] = dt.datetime.now().time().replace(microsecond=0)
            data['df']['latitude_leaving'] = message.location.latitude
            data['df']['longitude_leaving'] = message.location.longitude


        message_text = f'''Вы выехали из: \n<code>{data['df']['address_leaving']}</code>.\n\nТочка прибытия: \n<code>{data['df']['address_arriving']}</code>.\nПожалуйста, не забудьте <b><u>отметиться</u></b> при приезде.'''


        inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        buttons = [
            types.KeyboardButton(text='Приехал', request_location=True),
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
        data['df']['date_arriving'] = dt.datetime.now().date()
        data['df']['time_arriving'] = dt.datetime.now().time().replace(microsecond=0)
        data['df']['latitude_arriving'] = message.location.latitude
        data['df']['longitude_arriving'] = message.location.longitude
        data['df']['destination'] = distance(data['df']['latitude_leaving'], data['df']['longitude_arriving'], data['df']['latitude_arriving'], data['df']['longitude_arriving'])
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

    for user in admins:
        await bot.send_message(
        chat_id=user,
        text = message_text_for_admin,
        parse_mode=ParseMode.HTML
        )

    await Route.next()


async def getAct(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        async with state.proxy() as data:

            data['df']['act'] = 'no photo'
            fio = data['df']['surname'] + ' ' + data['df']['name']
            admins = data['admins']

        message_text_for_admin = f'{fio} не выложил фото Акта'
        for user in admins:
            await bot.send_message(
                chat_id=user,
                text=message_text_for_admin,
                parse_mode=ParseMode.HTML
            )

    else:

        async with state.proxy() as data:
            fio = data['df']['surname'] + ' ' + data['df']['name']
            path = os.getenv('path_', 'default')
            dir = rf'''\{path}\{fio}'''
            name = rf'{dir}\acts\act_{str(message.from_user.id)}_{dt.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.jpg'
            
            if not os.path.isdir(dir):
                os.mkdir(dir)
            if not os.path.isdir(dir+fr'\acts'):
                os.mkdir(dir+fr'\acts')

            await message.photo[-1].download(name)
            data['df']['act'] = name

            admins = data['admins']

        message_text_for_admin = f'{fio}  выложил фото Акта'
        for user in admins:
            await bot.send_message(
                chat_id=user,
                text=message_text_for_admin,
                parse_mode=ParseMode.HTML
            )


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Нет ТРН'),
        types.KeyboardButton(text='Отмена')
    ]

    message_text = f'''Спасибо! \nОтправьте фото ТРН'''
    await bot.send_message(
        chat_id=message.from_user.id,
        text=message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons)
    )


    await Route.next()


async def getTrn(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        async with state.proxy() as data:

            data['df']['trn'] = 'no photo'
            fio = data['df']['surname'] + ' ' + data['df']['name']
            admins = data['admins']

        message_text_for_admin = f'{fio} не выложил фото ТРН'
        for user in admins:
            await bot.send_message(
                chat_id=user,
                text=message_text_for_admin,
                parse_mode=ParseMode.HTML
            )

    else:

        async with state.proxy() as data:
            fio = data['df']['surname'] + ' ' + data['df']['name']
            path = os.getenv('path_', 'default')
            dir = rf'\{path}\{fio}'
            name = rf'{dir}\trns\trn_{str(message.from_user.id)}_{dt.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.jpg'
            
            if not os.path.isdir(dir):
                os.mkdir(dir)
            if not os.path.isdir(dir+fr'\trns'):
                os.mkdir(dir+fr'\trns')

            await message.photo[-1].download(name)
            data['df']['trn'] = name
            admins = data['admins']

        message_text_for_admin = f'{fio} выложил фото ТРН'
        for user in admins:
            await bot.send_message(
                chat_id=user,
                text=message_text_for_admin,
                parse_mode=ParseMode.HTML
            )


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Нет накладной'),
        types.KeyboardButton(text='Отмена')
    ]

    message_text = f'''Спасибо! \nОтправьте фото накладной'''
    await bot.send_message(
        chat_id=message.from_user.id,
        text=message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons)
    )

    await Route.next()


async def getConsignment(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        async with state.proxy() as data:
            data['df']['consignment'] = 'no photo'
            admins = data['admins']
            fio = data['df']['surname'] + ' ' + data['df']['name']

        message_text_for_admin = f'{fio} не выложил фото накдладной'
        for user in admins:
            await bot.send_message(
                chat_id=user,
                text=message_text_for_admin,
                parse_mode=ParseMode.HTML
            )

    else:

        async with state.proxy() as data:
            fio = data['df']['surname'] + ' ' + data['df']['name']
            path = os.getenv('path_', 'default')
            dir = rf'\{path}\{fio}'
            name = rf'{dir}\consignments\consignment_{str(message.from_user.id)}_{dt.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.jpg'

            if not os.path.isdir(dir):
                os.mkdir(dir)
            if not os.path.isdir(dir+fr'\consignments'):
                os.mkdir(dir+fr'\consignments')

            await message.photo[-1].download(name)
            data['df']['consignment'] = name
            admins = data['admins']


        message_text_for_admin = f'{fio} выложил фото накдладной'
        for user in admins:
            await bot.send_message(
                chat_id=user,
                text=message_text_for_admin,
                parse_mode=ParseMode.HTML
            )

            


    inkb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton(text='Выезд', request_location=True),
        types.KeyboardButton(text='Отмена')
    ]

    message_text = f'''Как будете выезжать нажмите кнопку выезд.'''
    await bot.send_message(
        chat_id=message.from_user.id,
        text=message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons)
    )

    async with state.proxy() as data:
        await db.insertOneRide(data['df'])

    await Route.location.set()


async def finishRoute(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['df']['time_leaving'] = dt.datetime.now().replace(microsecond=0)
        data['df']['latitude_leaving'] = message.location.latitude
        data['df']['longitude_leaving'] = message.location.longitude
        data['df']['address_leaving'] = next(data['route'])
        data['df']['address_arriving'] = next(data['route'])
        data['df']['destination'] = distance(data['df']['latitude_leaving'], data['df']['longitude_arriving'], data['df']['latitude_arriving'], data['df']['longitude_arriving'])
        data['df']['act'] = 'no photo'
        data['df']['trn'] = 'no photo'
        data['df']['consignment'] = 'no photo'


        admins = data['admins']
        route = data['route'].to_list
        message_text_for_admin = f'''Водитель: {data['df']['surname']} {data['df']['name']} {data['df']['patronymic']}, закончил поездку по маршруту №{data['df']['id_route']} ({route[0]} -> {route[-1]})'''
    

    await bot.send_message(
        chat_id=message.from_user.id,
        text='Поздравляем, вы завершили маршрут! \nНажмите на /start, чтобы посмотреть список открытых маршрутов.',
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove(),
    )

    for user in admins:
        await bot.send_message(
            chat_id=user,
            text=message_text_for_admin,
            parse_mode=ParseMode.HTML,
            )
        
    async with state.proxy() as data:
        await db.insertOneRide(data['df'])
        await db.deleteCatalogRoute({'driver': data['df']['id_user'], 'route': data['df']['id_route']})

        fio = data['df']['surname'] + ' ' + data['df']['name']
        path = os.getenv('path_', 'default')
        dir = rf'\{path}\{fio}'
        name = rf'''\records\record_{str(message.from_user.id)}_{dt.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.xlsx'''

        df = await db.getOneRecordRoute({'user': data['df']['id_user'], 'date': data['df']['date_leaving'], 
                                         'route': data['df']['id_route'], 'id': data['df']['id']})

        df = df.drop(columns=['id', 'id_user'])

        if not os.path.isdir(dir):
                os.mkdir(dir)
        if not os.path.isdir(dir+fr'\records'):
            os.mkdir(dir+fr'\records')

        df.rename(columns=names).to_excel(dir+name, index=False)
    
    await state.finish()


def register_handlers_clients(dp: Dispatcher):
    dp.register_callback_query_handler(getRoute, Text(equals='getRoute', ignore_case=True), state=None)
    dp.register_callback_query_handler(viewRoute, state=Route.df)
    dp.register_message_handler(startRoute, content_types=['location'], state=Route.location)
    dp.register_message_handler(getArriving, content_types=['location'], state=Route.arriving)
    dp.register_message_handler(getAct, content_types=['photo', 'text'], state=Route.act)
    dp.register_message_handler(getTrn, content_types=['photo', 'text'], state=Route.trn)
    dp.register_message_handler(getConsignment, content_types=['photo', 'text'], state=Route.consignment)
    dp.register_message_handler(finishRoute, content_types=['location'], state=Route.finish_route)
