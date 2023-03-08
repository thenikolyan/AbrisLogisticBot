import asyncio
from createBot import dp
from aiogram.utils import executor
from database import db, schema

from handlers import common


async def on_startup(_):
    db.dbCreate()
    print("Запустился!")


# clients.register_handlers_clients(dp)
# categories.register_handlers_clients(dp)
common.register_handlers_clients(dp)


if __name__ == "__main__":
    # start bot
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
