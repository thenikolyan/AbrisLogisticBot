from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
import os

from dotenv import load_dotenv
from pathlib import Path

#путь к файлу с данными для входа
dotenv_path = Path(rf'.\.env')
load_dotenv(dotenv_path=dotenv_path)

storage = MemoryStorage()

bot = Bot(token=os.getenv('token', 'default'))
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())
