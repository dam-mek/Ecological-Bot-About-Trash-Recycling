from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

import db.categories
import db.clients
import db.products
from bot import reply_keyboards
from bot.handlers.utils import delete_messages
from bot.messages import bot_responses
from bot.reply_keyboards import reply_keyboard_texts
from bot.middlewares import check_is_master


class MakingMaster(StatesGroup):
    telegram_id = State()
    verification = State()
    message_ids = State()


async def start_making_master(message: types.Message, state: FSMContext):
    bot_message = await message.answer(text='Введите код',
                                       reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(message_ids=[message.message_id, bot_message.message_id])
    await MakingMaster.telegram_id.set()


async def process_telegram_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.clients.make_master(int(message.text))
    await message.answer(f'{message.text} сделан админом', reply_markup=reply_keyboards.menu_master)
    await delete_messages(message.from_user.id, data['message_ids'] + [message.message_id])
    await state.finish()


async def process_invalid_telegram_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_message = await message.answer('Вводите только цифры')
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])


def register_handlers_making_master(dp: Dispatcher):
    dp.register_message_handler(start_making_master, check_is_master,
                                Text(equals=reply_keyboard_texts['menu master']['add master'], ignore_case=True), state='*')
    dp.register_message_handler(process_telegram_id, regexp=r'^\d*$', state=MakingMaster.telegram_id)
    dp.register_message_handler(process_invalid_telegram_id, state=MakingMaster.telegram_id)
