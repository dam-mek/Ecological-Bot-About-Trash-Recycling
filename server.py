import logging
from urllib.parse import urljoin
import os

from aiogram import Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from aiohttp import web
from bot.middlewares import AccessMiddleware
from bot.handlers.handlers import register_handlers
from bot.bot_commands import set_commands
from aiogram.dispatcher.webhook import get_new_configured_app
from bot.bot import bot

logging.basicConfig(level=logging.INFO)

dp = Dispatcher(bot, storage=MemoryStorage())
# dp.middleware.setup(AccessMiddleware())
register_handlers(dp)

PROJECT_NAME = os.getenv('PROJECT_NAME')  # Set it as you've set TOKEN env var

WEBHOOK_HOST = f'https://{PROJECT_NAME}.herokuapp.com/'  # Enter here your link from Heroku project settings
WEBHOOK_URL_PATH = '/webhook/' + os.getenv('TOKENPIDARASBOT')
WEBHOOK_URL = urljoin(WEBHOOK_HOST, WEBHOOK_URL_PATH)
WEBHOOK_HOST = 'https://{}.herokuapp.com/'


async def on_startup(app):
    """Simple hook for aiohttp application which manages webhook"""
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)
    await set_commands(dp)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(set_commands(bot))
    # loop.run_until_complete(bot.send_message(ADMIN_ID, 'I am ready'))
    # executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=shutdown)
    print('les go')

    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)
    app.on_startup.append(on_startup)
    # dp.loop.set_task_factory(context.task_factory)
    web.run_app(app, host='0.0.0.0', port=os.getenv('PORT'))
