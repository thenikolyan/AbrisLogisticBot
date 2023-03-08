from aiogram.types import ParseMode, InlineKeyboardButton
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup


from aiogram.utils.markdown import text, bold
from createBot import bot
from database import db


class User(StatesGroup):
    initials = State()
    end = State()


async def welcome(message: types.Message, state: FSMContext):
    await state.finish()
    await message.delete()
    
    message_text = text(f'Добро пожаловать, {message.from_user.username}!')

    inkb = types.InlineKeyboardMarkup(row_width=1)
    button = [
        types.InlineKeyboardButton(text='Зарегистрироваться', callback_data='addUser'),
        InlineKeyboardButton(text='Отмена', callback_data='cancel'),
    ]
    user = await db.getIdRoleUser(message.from_user.id)
    if user.empty:
        await bot.send_message(
            message.from_user.id,
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=inkb.add(*button),
        )
    else:
        user = user.to_dict('records')[0]
        
        if user['role'] == 'admin':
            await bot.send_message(
                message.from_user.id,
                message_text + ' Ваша роль: администратор.',
                parse_mode=ParseMode.MARKDOWN,
                #reply_markup=inkb.add(*button),
            )
        elif user['role'] == 'driver':
            await bot.send_message(
                message.from_user.id,
                message_text + ' Ваша роль: водитель.',
                parse_mode=ParseMode.MARKDOWN,
                #reply_markup=inkb.add(*button),
            )
        elif user['role'] == 'unauthtorized':
            await bot.send_message(
                message.from_user.id,
                message_text + '\nОжидайте подтвеждение администратора.',
                parse_mode=ParseMode.MARKDOWN,
                #reply_markup=inkb.add(*button),
            )
        else:
                await bot.send_message(
                message.from_user.id,
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=inkb.add(*button),
            )


async def initials(callback: types.CallbackQuery, state=None):
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    
    await state.finish()
    await User.initials.set()

    message_text = text(f'''Введите ваше ФИО. \nПример: «{bold('Иванов Иван Иванович')}»''')

    inkb = types.InlineKeyboardMarkup(row_width=2)
    button = [types.InlineKeyboardButton(text='Отмена', callback_data='cancel')]
    
    await bot.send_message(
        callback.from_user.id,
        message_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*button),
    )

    await User.next()


# async def role(message: types.Message, state: FSMContext):
#     await bot.delete_message(message.from_user.id, message.message_id-1)

#     async with state.proxy() as data:
#         data['initials'] = message.text

#     message_text = text(f'''Выбирите роль для регистрируемого пользователя:''')

#     inkb = types.InlineKeyboardMarkup(row_width=2)
#     button = [types.InlineKeyboardButton(text='Водитель', callback_data='driver'),
#               types.InlineKeyboardButton(text='Администратор', callback_data='admin'),
#               types.InlineKeyboardButton(text='Отмена', callback_data='cancel')]

#     await bot.send_message(
#         message.from_user.id,
#         message_text,
#         parse_mode=ParseMode.MARKDOWN,
#         reply_markup=inkb.add(*button),
#     )

#     await User.next()


async def goodbye(message: types.Message, state: FSMContext):
    await bot.delete_message(message.from_user.id, message.message_id)

    message_text = text(f'''Вы подали заявку на регистрацию в системе. \nОжидайте подтвеждение администратора.''')

    if len(message.text.split(' ')) == 3:
        fio = message.text.split(' ')[:3] 
        await db.insertUser({'id': message.from_user.id,
                            'name': fio[1],
                            'surname': fio[0],
                            'second_name': fio[2],
                            'role': 'unauthtorized',
                            }, db.engine)
        
        await bot.send_message(
        message.from_user.id,
        message_text,
        parse_mode=ParseMode.MARKDOWN
    )
    else:
        await bot.send_message(
        message.from_user.id,
        'Неправильно задано ФИО, начните заново /start',
        parse_mode=ParseMode.MARKDOWN
    )

    await state.finish()


async def cancel(callback: types.CallbackQuery, state: FSMContext):
    # current_state = await state.get_state()
    # if current_state is None:
    #     return
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    await state.finish()
    await callback.answer('Отмена предыдущего действия')
    

def register_handlers_clients(dp: Dispatcher):
    dp.register_message_handler(welcome, commands="start")
    dp.register_callback_query_handler(initials, Text(equals='addUser', ignore_case=True), state=None)
    dp.register_message_handler(goodbye, content_types=['text'], state=User.end)


    dp.register_callback_query_handler(cancel, Text(equals='cancel', ignore_case=True), state='*')