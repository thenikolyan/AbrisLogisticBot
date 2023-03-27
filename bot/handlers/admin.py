import time

from aiogram.types import ParseMode, InlineKeyboardButton
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from tabulate import tabulate

from aiogram.utils.markdown import text, bold
from createBot import bot
from database import db


class Role(StatesGroup):
    start = State()
    end = State()


class Route(StatesGroup):
    length = State()
    address = State()


class SettingRoute(StatesGroup):
    id_driver = State()
    id_route = State()


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
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*buttons),
    )


async def approveRegistration(callback: types.CallbackQuery, state=None):
    await state.finish()
    await Role.start.set()

    users = await db.getUnauthorizedUsers()

    if not users.empty:
        await bot.send_message(
            callback.from_user.id,
            text=f'<code>{users.to_markdown(index=False)}</code>',
            parse_mode=ParseMode.HTML,
        )
        await bot.send_message(
            callback.from_user.id,
            'Внесите id пользователя, регистрацию которого необходимо назначить (цифрами) и роль (admin/driver)\n Пример: 123445678 admin',
        )

        await Role.next()
    else:
        await bot.send_message(
            callback.from_user.id,
            'На данный момент никто не ждет подтверждения регистрации.',
        )
        await state.finish()
        await controlPanel(callback)


async def setRole(message: types.Message, state: FSMContext):
    id, role = message.text.split(' ')
    if role in ['admin', 'driver']:

        await db.updateUserRole({'id': id, 'role': role})
        message_text = f''' Пользователю c id {id} присвоена роль {role} '''

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
        await bot.send_message(
            int(id),
            f'Вам присвоена роль {role}.\n'
            f'Чтобы начать работу, нажмите /start'
        )
        await state.finish()
        await controlPanel(message)
    else:

        await bot.send_message(
            message.from_user.id,
            'Не верно введена роль.',
            parse_mode=ParseMode.MARKDOWN,
        )
        await approveRegistration(message, state)


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
        text=f'Введите длину маршрута',
        parse_mode=ParseMode.HTML,
    )


async def recordLengthRoute(message: types.Message, state: FSMContext):
    try:
        length = int(message.text)
        if length <= 1:
            await bot.send_message(
                message.from_user.id,
                text=f'Не верно введена длина, пожалуйста используйте цифры',
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

    await bot.send_message(
        message.from_user.id,
        text=f'Введите следующую точку маршрута',
        parse_mode=ParseMode.HTML
    )

    if data['length'] > 0:
        await Route.address.set()


    else:
        await db.insertRoute({'route': data['address'][:-1]}, db.engine)
        await bot.send_message(
            message.from_user.id,
            text=data['address'][:-1],
            parse_mode=ParseMode.HTML
        )
        await state.finish()
        await controlPanel(message)


async def setRoute(callback: types.CallbackQuery, state=None):
    await state.finish()
    drivers = await db.getDrivers()
    await bot.send_message(
        callback.from_user.id,
        text='Список водителей',
        parse_mode=ParseMode.HTML,
    )

    if not drivers.empty:
        await bot.send_message(
            callback.from_user.id,
            text=f'<code>{drivers.to_markdown(index=False)}</code>',
            parse_mode=ParseMode.HTML,
        )
    await bot.send_message(
        callback.from_user.id,
        text='Введите id водителя, которого хотите назначить',
        parse_mode=ParseMode.HTML,
    )
    await SettingRoute.id_driver.set()


async def chooseDriver(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['id_driver'] = int(message.text)
    except ValueError:
        await bot.send_message(
            message.from_user.id,
            text=f'Не верно введен символ, пожалуйста используйте цифры',
            parse_mode=ParseMode.HTML,
        )
        await setRoute(message)
    await bot.send_message(
        message.from_user.id,
        text='Список маршрутов',
        parse_mode=ParseMode.HTML,
    )
    routes = await db.getRoutes()
    if not routes.empty:
        await bot.send_message(
            message.from_user.id,
            text=f'<code>{routes.to_markdown(index=False)}</code>',
            parse_mode=ParseMode.HTML,
        )

    await bot.send_message(
        message.from_user.id,
        text='Введите id маршрута, которого хотите назначить',
        parse_mode=ParseMode.HTML,
    )

    await SettingRoute.id_route.set()


async def chooseRoute(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['id_route'] = int(message.text)
    except ValueError:
        await bot.send_message(
            message.from_user.id,
            text=f'Не верно введен символ, пожалуйста используйте цифры',
            parse_mode=ParseMode.HTML,
        )
        await setRoute(message)
    async with state.proxy() as data:
        await db.insertDriverRoute({'id_driver': data['id_driver'], 'id_route': data['id_route']}, db.engine)
    await bot.send_message(
        message.from_user.id,
        text=f'Вы назначили маршрут',
        parse_mode=ParseMode.HTML,
    )
    await state.finish()
    await controlPanel(message)


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
    dp.register_message_handler(setRole, content_types=['text'], state=Role.end)
    dp.register_callback_query_handler(driversList, Text(equals='driversList', ignore_case=True), state=None)

    dp.register_callback_query_handler(createRoute, Text(equals='createRoute', ignore_case=True), state=None)
    dp.register_message_handler(recordLengthRoute, content_types=['text'], state=Route.length)
    dp.register_message_handler(recordAddressRoute, content_types=['text'], state=Route.address)

    dp.register_callback_query_handler(setRoute, Text(equals='setRoute', ignore_case=True))
    dp.register_message_handler(chooseDriver, content_types=['text'], state=SettingRoute.id_driver)
    dp.register_message_handler(chooseRoute, content_types=['text'], state=SettingRoute.id_route)

    dp.register_callback_query_handler(routesList, Text(equals='routesList', ignore_case=True))
    dp.register_callback_query_handler(routesListDrivers, Text(equals='routesListDrivers', ignore_case=True))
