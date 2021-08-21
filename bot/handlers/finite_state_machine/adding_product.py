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


class AddingProduct(StatesGroup):
    name = State()
    price = State()
    verification = State()
    message_ids = State()


async def start_adding_product(message: types.Message, state: FSMContext):
    bot_message = await message.answer(text='Введите название товара',
                                       reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(message_ids=[message.message_id, bot_message.message_id])
    await AddingProduct.name.set()


async def process_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_message = await message.answer(text='Введите цену в баллах',
                                       reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await state.update_data(name=message.text)
    await AddingProduct.price.set()


async def process_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_message = await message.answer(text=f"Добавить товар «{data['name']}» по цене {message.text} бал.?", reply_markup=reply_keyboards.verification)
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await state.update_data(price=int(message.text))
    await AddingProduct.verification.set()


async def process_invalid_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_message = await message.answer(text='Введите цену, используя только цифры')
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])


async def process_verification(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == 'Да':
        db.products.add_product(data['name'], data['price'])
        txt = f"Товар {data['name']} с ценой {data['price']} добавлен"
        bot_message = await message.answer(text=txt,
                                           reply_markup=reply_keyboards.menu_master)
        await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
        await state.finish()
        return
    bot_message = await message.answer(text='Операция отменена',
                                       reply_markup=reply_keyboards.menu_master)
    await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
    await state.finish()


def register_handlers_adding_product(dp: Dispatcher):
    dp.register_message_handler(start_adding_product, check_is_master,
                                Text(equals=reply_keyboard_texts['menu master']['add product'], ignore_case=True), state='*')
    dp.register_message_handler(process_name, state=AddingProduct.name)
    dp.register_message_handler(process_price, regexp=r'^\d*$', state=AddingProduct.price)
    dp.register_message_handler(process_invalid_price, state=AddingProduct.price)
    dp.register_message_handler(process_verification, state=AddingProduct.verification)
