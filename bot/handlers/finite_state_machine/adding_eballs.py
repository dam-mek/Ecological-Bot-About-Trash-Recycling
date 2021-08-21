from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

import db.categories
import db.clients
from bot import reply_keyboards
from bot.handlers.utils import delete_messages
from bot.messages import bot_responses
from bot.reply_keyboards import reply_keyboard_texts

from bot.middlewares import check_is_master

class AddingEballs(StatesGroup):
    category = State()
    weight = State()
    telegram_id = State()
    verification = State()
    message_ids = State()


async def start_adding_eballs(message: types.Message, state: FSMContext):
    categories = db.categories.get_categories()
    response_text = bot_responses['categories']['introduction']
    list_for_reply_keyboard = []
    for category in categories:
        response_text += bot_responses['categories']['row in list'].format(category_name=category.name,
                                                                           category_icon=category.icon,
                                                                           price_koef=category.price_koef) + '\n'
        list_for_reply_keyboard += [f'{category.icon} {category.name} {category.icon}']
    bot_message = await message.answer(text=response_text,
                                       reply_markup=reply_keyboards.create_reply_keyboards(list_for_reply_keyboard))
    await state.update_data(message_ids=[message.message_id, bot_message.message_id])
    await AddingEballs.category.set()


async def process_category(message: types.Message, state: FSMContext):
    text = message.text[2:-2] if len(message.text) > 4 else 'q'
    data = await state.get_data()
    if text not in map(lambda p: p.name, db.categories.get_categories()) and data.get('category') is None:
        bot_message = await message.answer(text='Несуществуещая категория, выберите снова')
        await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
        await start_adding_eballs(message, state)
        return

    bot_message = await message.answer(text='Введите вес мусора в граммов (вес должен быть кратен 50 граммам)',
                                       reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await state.update_data(category=text)
    await AddingEballs.weight.set()


async def process_weight(message: types.Message, state: FSMContext):
    data = await state.get_data()
    txt = f"Введите код, который назовёт клиент"
    bot_message = await message.answer(text=txt)
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await state.update_data(weight=int(message.text))
    await AddingEballs.telegram_id.set()


async def process_invalid_weight(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_message = await message.answer(text='Вес должен быть кратен 50 граммам')
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])


async def process_telegram_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = message.text
    if int(code) in [client.telegram_id for client in db.clients.get_clients()]:
        txt = f"Информация верная?\nКатегория мусора: <b>{data['category']}</b>\nВес: <b>{data['weight']}</b>\nКод: <b>{code}</b>"
        bot_message = await message.answer(text=txt,
                                           reply_markup=reply_keyboards.verification)
        await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
        await state.update_data(telegram_id=int(message.text))
        await AddingEballs.verification.set()
    else:
        txt = f"Такого нет в нашей базе данных"
        bot_message = await message.answer(text=txt)
        await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])


async def process_verification(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == 'Да':
        db.categories.add_taken_trash(data['telegram_id'], data['category'], data['weight'])
        amount, difference = db.categories.add_eballs(data['telegram_id'], data['category'], data['weight'])
        txt = f"Операция совершена.\nСчёт клиента: <b>{amount} бал. (добавлено {difference})</b>\nКатегория: <b>{data['category']}</b>\nВес: <b>{data['weight']}</b>"
        bot_message = await message.answer(text=txt,
                                           reply_markup=reply_keyboards.menu_master)
        await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
        await state.finish()
        return
    bot_message = await message.answer(text='Ок, отменяем',
                                       reply_markup=reply_keyboards.menu_master)
    await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
    await state.finish()


async def process_invalid_telegram_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_message = await message.answer(text='Код состоит только из цифр')
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])


def register_handlers_adding_eballs(dp: Dispatcher):
    dp.register_message_handler(start_adding_eballs, check_is_master,
                                Text(equals=reply_keyboard_texts['menu master']['add trash'], ignore_case=True), state='*')
    dp.register_message_handler(process_category, state=AddingEballs.category)
    dp.register_message_handler(process_weight, regexp=r'^\d*[50]0+$', state=AddingEballs.weight)
    dp.register_message_handler(process_invalid_weight, state=AddingEballs.weight)
    dp.register_message_handler(process_telegram_id, regexp=r'^\d*$', state=AddingEballs.telegram_id)
    dp.register_message_handler(process_invalid_telegram_id, state=AddingEballs.telegram_id)
    dp.register_message_handler(process_verification, state=AddingEballs.verification)
