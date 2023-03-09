from aiogram.types import ParseMode, InlineKeyboardButton
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup


from aiogram.utils.markdown import text, bold
from createBot import bot
from database import db


# async def chooseDirect()
#
# def register_handlers_clients(dp: Dispatcher):
#     dp.register_callback_query_handler(chooseDirect, Text(equals='chooseDirect', ignore_case=True), state=None)
