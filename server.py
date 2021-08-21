import logging

from aiogram import Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot.middlewares import AccessMiddleware
from bot.handlers.handlers import register_handlers
from bot.bot_commands import set_commands
from bot.bot import bot

logging.basicConfig(level=logging.INFO)

dp = Dispatcher(bot, storage=MemoryStorage())
# dp.middleware.setup(AccessMiddleware())
register_handlers(dp)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(set_commands(bot))
    # loop.run_until_complete(bot.send_message(ADMIN_ID, 'I am ready'))
    print('les go')
    executor.start_polling(dp, skip_updates=True, on_startup=set_commands, on_shutdown=shutdown)
