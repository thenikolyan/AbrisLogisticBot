import os

from aiogram.types import ParseMode
from aiogram.types.input_file import InputFile
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

import pandas as pd
import sqlalchemy

from auxiliary.catalog import names
from createBot import bot
from database import db


class Role(StatesGroup):
    id = State()
    role = State()
    end = State()


class Route(StatesGroup):
    length = State()
    address = State()


class RouteExcel(StatesGroup):
    excel = State()


class DeleteRoute(StatesGroup):
    id = State()


class SettingRoute(StatesGroup):
    routes = State()
    id_route = State()
    id_driver = State()


# Control panels
async def controlPanel(callback: types.CallbackQuery, state='*'):
    await state.finish()
    try:
        await bot.delete_message(callback.from_user.id, callback.message.message_id)
    except AttributeError:
        pass
    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton(text='Подтверждение регистрации', callback_data='approveRegistration'),
        types.InlineKeyboardButton(text='Просмотр каталогов', callback_data='controlPanelViewCatalog'),
        types.InlineKeyboardButton(text='Работа с маршрутами', callback_data='controlPanelRoute'),
        types.InlineKeyboardButton(text='Сбор отчета', callback_data='createReport'),
        types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
    ]

    await bot.send_message(
        callback.from_user.id,
        'Панель управления',
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons),
    )


async def controlPanelViewCatalog(callback: types.CallbackQuery, state='*'):
    await state.finish()
    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [types.InlineKeyboardButton(text='Просмотр списка водителей', callback_data='driversList'),
               types.InlineKeyboardButton(text='Просмотр списка маршрутов', callback_data='routesList'),
               types.InlineKeyboardButton(text='Просмотр списка маршрутов с водителями', callback_data='routesListDrivers'),
               types.InlineKeyboardButton(text='Назад', callback_data='controlPanel')]
    
    await bot.send_message(
        callback.from_user.id,
        'Панель управления маршрутами',
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons),
    )


async def controlPanelRoute(callback: types.CallbackQuery, state='*'):
    await state.finish()
    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [types.InlineKeyboardButton(text='Создать маршрут', callback_data='chooseWayCreateRoute'),
               types.InlineKeyboardButton(text='Назначить маршрут', callback_data='setRoute'),
               types.InlineKeyboardButton(text='Удалить маршрут', callback_data='deleteRoute'),
               types.InlineKeyboardButton(text='Назад', callback_data='controlPanel')]
    
    await bot.send_message(
        callback.from_user.id,
        'Панель управления маршрутами',
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons),
    )


# Approve registration
async def approveRegistration(callback: types.CallbackQuery, state=None):
    await state.finish()
    await Role.id.set()

    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    users = await db.getUnauthorizedUsers()
    if not users.empty:
        users = users.sort_values(by='surname', ascending=False)

        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = []

        for x in users.to_dict('records'):
            buttons.append(types.InlineKeyboardButton(text=f'''{x['surname']} {x['name']} {x['patronymic']}''',
                                                      callback_data=str(x['id'])))
        buttons.append(types.InlineKeyboardButton(text='Отмена', callback_data='cancel'))

        await bot.send_message(
            callback.from_user.id,
            'Выберите пользователя, которому хотите назначить роль.',
            parse_mode=ParseMode.HTML,
            reply_markup=inkb.add(*buttons)
        )

        await Role.next()
    else:
        await bot.send_message(
            callback.from_user.id,
            'На данный момент, никто не ожидает подтверждения регистрации.',
        )
        await state.finish()
        await controlPanel(callback, state=None)


async def setRole(callback: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    async with state.proxy() as data:
        data['id'] = callback.data

    message_text = 'Пожалуйста, выберите роль.'

    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton(text='Администратор', callback_data='admin'),
        types.InlineKeyboardButton(text='Водитель', callback_data='driver'),
        types.InlineKeyboardButton(text='Не показывать', callback_data='clown'),
        types.InlineKeyboardButton(text='Отмена', callback_data='cancel'),
    ]
    await bot.send_message(
        callback.from_user.id,
        message_text,
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons),
    )

    await Role.next()


async def endRole(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['role'] = callback.data

    message_text = f'''Вам присвоена роль «<b>{data['role']}</b>». \nНажмите /start для продолжения работы.'''
    message_text_for_admin = f'''Роль «<b>{data['role']}</b>» успешно присвоена.'''

    await db.updateUserRole({'id': int(data['id']), 'role': data['role']})

    await bot.send_message(
        int(data['id']),
        message_text,
        parse_mode=ParseMode.HTML,
    )

    await bot.send_message(
        callback.from_user.id,
        message_text_for_admin,
        parse_mode=ParseMode.HTML,
    )

    await state.finish()
    await controlPanel(callback, state=None)


# Viewing catalogs
async def driversList(callback: types.CallbackQuery):
    drivers = await db.getDrivers()
    if not drivers.empty:
        
        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton(text='Назад', callback_data='controlPanelViewCatalog')
        ]
        
        file_name = f'''tmp{str(hash('tmp'))}'''

        drivers.to_excel(f'''./bot/documents/{file_name}.xlsx''', index=False)

        message_text = 'Список водителей.'
        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [types.InlineKeyboardButton(text='Назад', callback_data='controlPanelViewCatalog')]
        
        await bot.send_document(chat_id=callback.from_user.id,
                                document=InputFile(f'''./bot/documents/{file_name}.xlsx'''),
                                caption=message_text,
                                reply_markup=inkb.add(*buttons)
                                )

        os.remove(f'''./bot/documents/{file_name}.xlsx''')

    else:
        await bot.send_message(
            callback.from_user.id,
            'На данный момент водителей нет в базе.',
        )


async def routesList(callback: types.CallbackQuery):
    routes = await db.getRoutes()
    if not routes.empty:
        file_name = f'''tmp{str(hash('tmp'))}'''

        routes.to_excel(f'''./bot/documents/{file_name}.xlsx''', index=False)

        message_text = 'Список маршрутов'
        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [types.InlineKeyboardButton(text='Назад', callback_data='controlPanelViewCatalog')]
        
        await bot.send_document(chat_id=callback.from_user.id,
                                document=InputFile(f'''./bot/documents/{file_name}.xlsx'''),
                                caption=message_text,
                                reply_markup=inkb.add(*buttons)
                                )

        os.remove(f'''./bot/documents/{file_name}.xlsx''')
    else:
        await bot.send_message(
            callback.from_user.id,
            text=f'Не создано ни одного маршрута.',
            parse_mode=ParseMode.HTML)


async def routesListDrivers(callback: types.CallbackQuery):
    catalog = await db.getCatalogRoute()
    if not catalog.empty:
        file_name = f'''tmp{str(hash('tmp'))}'''

        catalog.to_excel(f'''./bot/documents/{file_name}.xlsx''', index=False)

        message_text = 'Список водителей и их маршрутов.'
        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [types.InlineKeyboardButton(text='Назад', callback_data='controlPanelViewCatalog')]

        await bot.send_document(chat_id=callback.from_user.id,
                                document=InputFile(f'''./bot/documents/{file_name}.xlsx'''),
                                caption=message_text,
                                reply_markup=inkb.add(*buttons)
                                )

        os.remove(f'''./bot/documents/{file_name}.xlsx''')

    else:
        await bot.send_message(
            callback.from_user.id,
            text=f'Ни один маршрут не назначен.',
            parse_mode=ParseMode.HTML)


# Working with routes
async def chooseWayCreateRoute(callback: types.CallbackQuery, state='*'):
    await state.finish()
    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [types.InlineKeyboardButton(text='Создать вручную', callback_data='createRoute'),
               types.InlineKeyboardButton(text='Excel формат', callback_data='createRouteExcel'),
               types.InlineKeyboardButton(text='Назад', callback_data='controlPanelRoute')]
    
    await bot.send_message(
        callback.from_user.id,
        'Панель управления маршрутами',
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons),
    )    


## Create route
async def createRoute(callback: types.CallbackQuery, state=None):
    await state.finish()
    await Route.length.set()

    await bot.send_message(
        callback.from_user.id,
        text=f'Введите количество точек маршрута',
        parse_mode=ParseMode.HTML,
    )


async def recordLengthRoute(message: types.Message, state: FSMContext):
    try:
        length = int(message.text)
        if length <= 1:
            await bot.send_message(
                message.from_user.id,
                text=f'Не верно введено количество точек маршрута. \nМаршрут не может состоять из 1 или менее точек.',
                parse_mode=ParseMode.HTML,
            )
            await recordLengthRoute(message)
    except ValueError:
        await bot.send_message(
            message.from_user.id,
            text=f'Не верно введен символ, пожалуйста используйте цифры',
            parse_mode=ParseMode.HTML,
        )
        await recordLengthRoute(message)

    async with state.proxy() as data:
        data['length'] = length
        data['address'] = ''

    await bot.send_message(
        message.from_user.id,
        text=f'Введите первую точку маршрута',
        parse_mode=ParseMode.HTML
    )

    await Route.next()


async def recordAddressRoute(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['length'] -= 1
        data['address'] += f'''{message.text}~'''

    if data['length'] > 0:

        await bot.send_message(
            message.from_user.id,
            text=f'Введите следующую точку маршрута',
            parse_mode=ParseMode.HTML
        )

        await Route.address.set()

        
    else:
        await db.insertRoute({'route': data['address'][:-1]})
        await bot.send_message(
            message.from_user.id,
            text='Маршрут создан.',
            parse_mode=ParseMode.HTML
        )
        await state.finish()
        await controlPanel(message, state=None)


## Create route using excel
async def createRouteExcel(callback: types.CallbackQuery, state=None):
    await state.finish()

    message_text = 'Пожалуйста, <b>используйте шаблон</b> представленный в примере, для корректного ввода.'
    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [types.InlineKeyboardButton(text='Назад', callback_data='chooseWayCreateRoute')]

    await bot.send_document(chat_id=callback.from_user.id,
                            document=InputFile(f'''./bot/documents/examples/Пример маршрута.xlsx'''),
                            caption=message_text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=inkb.add(*buttons)
                            )
    
    await RouteExcel.excel.set()


async def insertRouteExcel(message: types.Message, state: FSMContext):
    if message.document.file_name.split('.')[-1] != 'xlsx':

        message_text = 'Неверный формат файла. Пожалуйста, используйте формат <b>«xlsx»</b>.'
        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [types.InlineKeyboardButton(text='Назад', callback_data='chooseWayCreateRoute')]

        await bot.send_message(chat_id=message.from_user.id,
                                text=message_text,
                                parse_mode=ParseMode.HTML,
                                reply_markup=inkb.add(*buttons)
                                )
    else:
        name = str(hash(message.document.file_name))
        await message.document.download(f'''./bot/documents/{name}.xlsx''')

        df = pd.read_excel(f'''./bot/documents/{name}.xlsx''')
        os.remove(f'''./bot/documents/{name}.xlsx''')

        try:
            route = '~'.join(list(df['Маршрут']))
            df = await db.getRoutes()
            print(df['route'])
            if route not in list(df['route']):
                await db.insertRoute({'route': route})
                await state.finish()
                message_text = 'Маршрут добавлен.'

                await bot.send_message(chat_id=message.from_user.id,
                                        text=message_text
                                        )
                
                await controlPanel(state=None)
            else:
                await state.finish()
                message_text = 'Такой маршрут уже существует. Пожалуйста, отправьте другой маршрут.'
                inkb = types.InlineKeyboardMarkup(row_width=1)
                buttons = [types.InlineKeyboardButton(text='Назад', callback_data='chooseWayCreateRoute')]
                await bot.send_message(chat_id=message.from_user.id,
                                        text=message_text,
                                        reply_markup=inkb.add(*buttons)
                                        )
            
        except KeyError:
            message_text = 'Неверное имя колонки. Пожалуйста, используйте имя для колонки, где записан маршрут, <b>«Маршрут»</b>.'
            inkb = types.InlineKeyboardMarkup(row_width=1)
            buttons = [types.InlineKeyboardButton(text='Назад', callback_data='chooseWayCreateRoute')]

            await bot.send_message(chat_id=message.from_user.id,
                                    text=message_text,
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=inkb.add(*buttons)
                                    )


# Set route
async def setRoute(callback: types.CallbackQuery, state=None):
    await state.finish()
    await SettingRoute.routes.set()

    routes = await db.getRoutes()
    file_name = f'''tmp{str(hash('tmp'))}'''

    routes.to_excel(f'''./bot/documents/{file_name}.xlsx''', index=False)

    message_text = 'Пожалуйста: \n1) Откройте файл \n2) Выбирите «ID» маршрута \n3) Введите «ID» маршрута'
    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [types.InlineKeyboardButton(text='Назад', callback_data='controlPanelRoute')]
    await bot.send_document(chat_id=callback.from_user.id,
                            document=InputFile(f'''./bot/documents/{file_name}.xlsx'''),
                            caption=message_text,
                            reply_markup=inkb.add(*buttons)
                            )

    async with state.proxy() as data:
        data['routes'] = routes

    await SettingRoute.next()

    os.remove(f'''./bot/documents/{file_name}.xlsx''')


async def chooseDriver(message: types.Message, state: FSMContext):

    try:
        async with state.proxy() as data:
            if not int(message.text) in list(data['routes'].id):

                inkb = types.InlineKeyboardMarkup(row_width=1)
                buttons = [types.InlineKeyboardButton(text='Назад', callback_data='controlPanelRoute')]

                await bot.send_message(
                    chat_id=message.from_user.id,
                    text='Не верный «ID» маршрута. \nПовторно введите «ID» маршрута.',
                    reply_markup=inkb.add(*buttons)
                )
                await chooseDriver()
            else:
                data['id_route'] = int(message.text)

        drivers = await db.getDrivers()
        if not drivers.empty:
            drivers = drivers.sort_values(by='surname', ascending=False)

            message_text = 'Выберите водителя, которому хотите назначить маршрут.'

            inkb = types.InlineKeyboardMarkup(row_width=1)
            buttons = []

            for x in drivers.to_dict('records'):
                buttons.append(types.InlineKeyboardButton(text=f'''{x['surname']} {x['name']} {x['patronymic']}''', callback_data=str(x['id'])))
            buttons.append(types.InlineKeyboardButton(text='Назад', callback_data='controlPanelRoute'))

            await bot.send_message(
                chat_id=message.from_user.id,
                text=message_text,
                parse_mode=ParseMode.HTML,
                reply_markup=inkb.add(*buttons)
            )
        else:
            await bot.send_message(
                message.from_user.id,
                'На данный момент нет ни одного водителя.'
            )
            await state.finish()

    except ValueError:

        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [types.InlineKeyboardButton(text='Назад', callback_data='controlPanelRoute')]

        await bot.send_message(
            chat_id=message.from_user.id,
            text='Введите <b>ЧИСЛО</b> без пробелов или спецсимволов.',
            parse_mode=ParseMode.HTML,
            reply_markup=inkb.add(*buttons)
        )
        await chooseDriver()

    await SettingRoute.next()


async def endSetRoute(callback: types.CallbackQuery, state: FSMContext):
    #await bot.delete_message(callback.from_user.id, callback.message.message_id)
    async with state.proxy() as data:
        data['id_driver'] = int(callback.data)

    try:
        await db.insertRouteCatalog({'driver': data['id_driver'], 'route': data['id_route']})
        message_text_for_admin = 'Маршрут назначен.'
        message_text = 'Вам назначен новый маршрут. Нажмите /start'

        await bot.send_message(
            chat_id=callback.from_user.id,
            text=message_text_for_admin
        )

        await bot.send_message(
            chat_id=data['id_driver'],
            text=message_text
        )

    except sqlalchemy.exc.IntegrityError:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text='Нельзя повторно назначать маршрут.'
        )

    await state.finish()
    await controlPanel(callback, state=None)


# Delete route
async def deleteRoute(callback: types.CallbackQuery, state=None):
    await state.finish()
    
    routes = await db.getRoutes()
    file_name = f'''tmp{str(hash('tmp'))}'''

    routes.to_excel(f'''./bot/documents/{file_name}.xlsx''', index=False)

    message_text = 'Пожалуйста: \n1) Откройте файл \n2) Выбирите «ID» маршрута \n3) Введите «ID» маршрута'
    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [types.InlineKeyboardButton(text='Назад', callback_data='controlPanelRoute')]
    await bot.send_document(chat_id=callback.from_user.id,
                            document=InputFile(f'''./bot/documents/{file_name}.xlsx'''),
                            caption=message_text,
                            reply_markup=inkb.add(*buttons)
                            )

    await DeleteRoute.id.set()

    os.remove(f'''./bot/documents/{file_name}.xlsx''')


async def finishDeleteRoute(message: types.Message, state: FSMContext):
    routes = await db.getRoutes()
    try:
        if not int(message.text) in list(routes['id']):

            inkb = types.InlineKeyboardMarkup(row_width=1)
            buttons = [types.InlineKeyboardButton(text='Назад', callback_data='controlPanelRoute')]

            await bot.send_message(
                chat_id=message.from_user.id,
                text='Не верный «ID» маршрута. \nПовторно введите «ID» маршрута.',
                reply_markup=inkb.add(*buttons)
            )
            await finishDeleteRoute()
        else:
            await db.deleteRoute({'id': int(message.text)})
            await bot.send_message(
                chat_id=message.from_user.id,
                text=f'''Маршрут №{message.text} удален.'''
            )

    except ValueError:

        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [types.InlineKeyboardButton(text='Назад', callback_data='controlPanelRoute')]

        await bot.send_message(
            chat_id=message.from_user.id,
            text='Введите <b>ЧИСЛО</b> без пробелов или спецсимволов.',
            parse_mode=ParseMode.HTML,
            reply_markup=inkb.add(*buttons)
        )
        await finishDeleteRoute()

    await state.finish()


# Create reports
async def createReport(callback: types.CallbackQuery):
    routes = await db.getAllRoute()
    if not routes.empty:
        routes = routes.drop(columns=['id', 'id_user'])

        file_name = f'''tmp{str(hash('tmp'))}'''

        routes.rename(columns=names).to_excel(f'''./bot/documents/{file_name}.xlsx''', index=False)

        message_text = 'Отчет о всех поездках.'
        await bot.send_document(chat_id=callback.from_user.id,
                                document=InputFile(f'''./bot/documents/{file_name}.xlsx'''),
                                caption=message_text
                                )

        os.remove(f'''./bot/documents/{file_name}.xlsx''')
    else:
        message_text = 'Не совершено ни одной поездки.'
        await bot.send_message(chat_id=callback.from_user.id,
                                text=message_text
                                )


def register_handlers_clients(dp: Dispatcher):
    dp.register_callback_query_handler(controlPanel, Text(equals='controlPanel', ignore_case=True), state='*')
    dp.register_callback_query_handler(controlPanelRoute, Text(equals='controlPanelRoute', ignore_case=True), state='*')
    dp.register_callback_query_handler(controlPanelViewCatalog, Text(equals='controlPanelViewCatalog', ignore_case=True), state='*')
    

    dp.register_callback_query_handler(approveRegistration, Text(equals='approveRegistration', ignore_case=True),state=None)
    dp.register_callback_query_handler(setRole, state=Role.role)
    dp.register_callback_query_handler(endRole, state=Role.end)


    dp.register_callback_query_handler(driversList, Text(equals='driversList', ignore_case=True))
    dp.register_callback_query_handler(routesList, Text(equals='routesList', ignore_case=True))
    dp.register_callback_query_handler(routesListDrivers, Text(equals='routesListDrivers', ignore_case=True))


    dp.register_callback_query_handler(chooseWayCreateRoute, Text(equals='chooseWayCreateRoute', ignore_case=True), state='*')

    dp.register_callback_query_handler(createRoute, Text(equals='createRoute', ignore_case=True), state=None)
    dp.register_message_handler(recordLengthRoute, content_types=['text'], state=Route.length)
    dp.register_message_handler(recordAddressRoute, content_types=['text'], state=Route.address)

    dp.register_callback_query_handler(createRouteExcel, Text(equals='createRouteExcel', ignore_case=True), state=None)
    dp.register_message_handler(insertRouteExcel, content_types=['document'], state=RouteExcel.excel)

    dp.register_callback_query_handler(setRoute, Text(equals='setRoute', ignore_case=True))
    dp.register_message_handler(chooseDriver, content_types=['text'], state=SettingRoute.id_route)
    dp.register_callback_query_handler(endSetRoute, state=SettingRoute.id_driver)

    dp.register_callback_query_handler(deleteRoute, Text(equals='deleteRoute', ignore_case=True), state=None)
    dp.register_message_handler(finishDeleteRoute, content_types=['text'], state=DeleteRoute.id)


    dp.register_callback_query_handler(createReport, Text(equals='createReport', ignore_case=True))
