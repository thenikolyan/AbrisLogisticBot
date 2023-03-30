
import os
import time

from aiogram.types import ParseMode
from aiogram.types.input_file import InputFile
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from tabulate import tabulate
import sqlalchemy
from aiogram.utils.markdown import text, bold
from createBot import bot
from database import db


class Role(StatesGroup):
    id = State()
    role = State()
    end = State()


class Route(StatesGroup):
    length = State()
    address = State()


class SettingRoute(StatesGroup):
    routes = State()
    id_route = State()
    id_driver = State()


async def controlPanel(callback: types.CallbackQuery):
    try:
        await bot.delete_message(callback.from_user.id, callback.message.message_id)
    except AttributeError:
        pass
    inkb = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton(text='Просмотр списка водителей', callback_data='driversList'),
        types.InlineKeyboardButton(text='Подтверждение регистрации', callback_data='approveRegistration'),
        types.InlineKeyboardButton(text='Просмотр списка маршрутов', callback_data='routesList'),
        types.InlineKeyboardButton(text='Просмотр списка маршрутов с водителями', callback_data='routesListDrivers'),
        types.InlineKeyboardButton(text='Создание маршрута', callback_data='createRoute'),
        types.InlineKeyboardButton(text='Назначить маршрут', callback_data='setRoute'),
        types.InlineKeyboardButton(text='Сбор отчета', callback_data='createReport'),
        types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
    ]

    await bot.send_message(
        callback.from_user.id,
        'Панель управления',
        parse_mode=ParseMode.HTML,
        reply_markup=inkb.add(*buttons),
    )


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
            buttons.append(types.InlineKeyboardButton(text=f'''{x['surname']} {x['name']} {x['second_name']}''',
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
        await controlPanel(callback)


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
    await controlPanel(callback)


async def driversList(callback: types.CallbackQuery):
    drivers = await db.getDrivers()
    if not drivers.empty:
        await bot.send_message(
            callback.from_user.id,
            text=f'<code>{drivers.to_markdown(index=False)}</code>',
            parse_mode=ParseMode.HTML,
        )
        inkb = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton(text='Назначить маршрут', callback_data='setRoute'),
            types.InlineKeyboardButton(text='Создать маршрут', callback_data='createRoute'),
            types.InlineKeyboardButton(text='Вернуться в главное меню', callback_data='controlPanel'),
            types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ]
        await bot.send_message(
            callback.from_user.id,
            'Выберете действие',
            reply_markup=inkb.add(*buttons)

        )
    else:
        await bot.send_message(
            callback.from_user.id,
            'На данный момент водителей нет в базе.',
        )

        await controlPanel(callback)


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
        await controlPanel(message)


# назначение маршрута
async def setRoute(callback: types.CallbackQuery, state=None):


    await state.finish()
    await SettingRoute.routes.set()

    routes = await db.getRoutes()
    file_name = f'''tmp{hash('tmp')}'''

    routes.to_excel(f'''./bot/documents/{file_name}.xlsx''', index=False)

    message_text = 'Пожалуйста: \n1) Откройте файл \n2) Выбирите «ID» маршрута \n3) Введите «ID» маршрута'

    await bot.send_document(chat_id=callback.from_user.id,
                            document=InputFile(f'''./bot/documents/{file_name}.xlsx'''),
                            caption=message_text
                            )

    async with state.proxy() as data:
        data['routes'] = routes

    await SettingRoute.next()

    os.remove(f'''./bot/documents/{file_name}.xlsx''')


async def chooseDriver(message: types.Message, state: FSMContext):

    try:
        async with state.proxy() as data:
            if not int(message.text) in list(data['routes'].id):
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text='Не верный «ID» маршрута. \nПовторно введите «ID» маршрута.'
                )
                await chooseDriver(message)
            else:
                data['id_route'] = int(message.text)
                print(data)

        drivers = await db.getDrivers()
        if not drivers.empty:
            drivers = drivers.sort_values(by='surname', ascending=False)

            message_text = 'Выберите водителя, которому хотите назначить маршрут.'

            inkb = types.InlineKeyboardMarkup(row_width=1)
            buttons = []

            for x in drivers.to_dict('records'):
                buttons.append(types.InlineKeyboardButton(text=f'''{x['surname']} {x['name']} {x['second_name']}''', callback_data=str(x['id'])))
            buttons.append(types.InlineKeyboardButton(text='Отмена', callback_data='cancel'))

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
            await controlPanel(message)

    except ValueError:

        await bot.send_message(
            chat_id=message.from_user.id,
            text='Введите <b>ЧИСЛО</b> без пробелов или спецсимволов.',
            parse_mode=ParseMode.HTML
        )
        await chooseDriver(message)

    await SettingRoute.next()


async def endSetRoute(callback: types.CallbackQuery, state: FSMContext):
    #await bot.delete_message(callback.from_user.id, callback.message.message_id)
    async with state.proxy() as data:
        data['id_driver'] = int(callback.data)

    try:
        await db.setRoute({'driver': data['id_driver'], 'route': data['id_route']})
        message_text_for_admin = 'Маршрут назначен.'
        message_text = 'Вам назначен новый маршрут.'

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
    await controlPanel(callback)


async def routesList(callback: types.CallbackQuery):
    routes = await db.getRoutes()
    if not routes.empty:
        await bot.send_message(
            callback.from_user.id,
            text=f'<code>{routes.to_markdown(index=False)}</code>',
            parse_mode=ParseMode.HTML)

    await controlPanel(callback)


async def routesListDrivers(callback: types.CallbackQuery):
    catalog = await db.getCatalogRoute()
    if not catalog.empty:
        await bot.send_message(
            callback.from_user.id,
            text=f'<code>{catalog.to_markdown(index=False)}</code>',
            parse_mode=ParseMode.HTML)
    else:
        await bot.send_message(
            callback.from_user.id,
            text=f'Нет данных.',
            parse_mode=ParseMode.HTML)

    await controlPanel(callback)


def register_handlers_clients(dp: Dispatcher):
    dp.register_callback_query_handler(controlPanel, Text(equals='controlPanel', ignore_case=True))

    dp.register_callback_query_handler(approveRegistration, Text(equals='approveRegistration', ignore_case=True),
                                       state=None)
    dp.register_callback_query_handler(setRole, state=Role.role)
    dp.register_callback_query_handler(endRole, state=Role.end)

    dp.register_callback_query_handler(driversList, Text(equals='driversList', ignore_case=True), state=None)

    dp.register_callback_query_handler(createRoute, Text(equals='createRoute', ignore_case=True), state=None)
    dp.register_message_handler(recordLengthRoute, content_types=['text'], state=Route.length)
    dp.register_message_handler(recordAddressRoute, content_types=['text'], state=Route.address)

    dp.register_callback_query_handler(setRoute, Text(equals='setRoute', ignore_case=True))
    dp.register_message_handler(chooseDriver, content_types=['text'], state=SettingRoute.id_route)
    dp.register_callback_query_handler(endSetRoute, state=SettingRoute.id_driver)

    dp.register_callback_query_handler(routesList, Text(equals='routesList', ignore_case=True))
    dp.register_callback_query_handler(routesListDrivers, Text(equals='routesListDrivers', ignore_case=True))
