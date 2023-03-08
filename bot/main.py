import os
from dotenv import load_dotenv
from pathlib import Path

from pyrogram import Client

#путь к файлу с данными для входа
dotenv_path = Path(rf'C:\Users\PythonN\Desktop\AbrisLogisticBot\.env')
load_dotenv(dotenv_path=dotenv_path)

#переменные для запуска бота
api_id = os.getenv('api_id', 'default')
api_hash = os.getenv('api_hash', 'default')
bot_token = os.getenv('token', 'default')

app = Client("AbrisLogisticBot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


app.start()

app.send_message(chat_id="@thenikolyan", text="Напиши, если сообщение пришло")

app.stop()