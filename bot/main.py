import asyncio
from createBot import dp
from aiogram.utils import executor
from database import db, schema

from handlers import general, admin, driver

async def on_startup(_):
    db.dbCreate()
    print("Запустился!")


general.register_handlers_clients(dp)
admin.register_handlers_clients(dp)
driver.register_handlers_clients(dp)


if __name__ == "__main__":
    # start bot
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
 