import aiogram
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.utils.exceptions import CantParseEntities
from bot import reply_keyboards
from bot.reply_keyboards import reply_keyboard_texts
from bot.messages import bot_responses
from bot.handlers.utils import delete_messages, process_error
from db import db


class AddingIncome(StatesGroup):
    amount = State()
    category = State()
    label = State()
    date = State()
    place = State()
    description = State()
    verification = State()
    message_ids = State()


async def start_reply_adding_income(message: types.Message, state: FSMContext):
    bot_message = await message.answer(text=bot_responses['adding income']['amount'],
                                       reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(message_ids=[message.message_id, bot_message.message_id])
    await AddingIncome.amount.set()


async def process_amount(message: types.Message, state: FSMContext):
    try:
        await state.update_data(amount=float(message.text.replace(',', '.')))
    except ValueError as error:
        await process_error(error, message, state)
        return
    bot_message = await message.answer(text=bot_responses['adding income']['category'],
                                       reply_markup=reply_keyboards.get_category_reply_keyboard(message.chat.id))
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingIncome.next()


async def process_invalid_amount(message: types.Message, state: FSMContext):
    bot_message = await message.answer(text=bot_responses['adding income']['invalid amount'],
                                       reply_markup=types.ReplyKeyboardRemove())
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])


async def process_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    bot_message = await message.answer(text=bot_responses['adding income']['label'],
                                       reply_markup=reply_keyboards.get_label_reply_keyboard(message.chat.id))
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingIncome.next()


async def process_label(message: types.Message, state: FSMContext):
    await state.update_data(label=message.text)
    bot_message = await message.answer(text=bot_responses['adding income']['date'],
                                       reply_markup=reply_keyboards.dates)
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingIncome.next()


async def process_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    bot_message = await message.answer(text=bot_responses['adding income']['place'],
                                       reply_markup=reply_keyboards.places)
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingIncome.next()


async def process_place(message: types.Message, state: FSMContext):
    await state.update_data(place=message.text)
    bot_message = await message.answer(text=bot_responses['adding income']['description'],
                                       reply_markup=reply_keyboards.description)
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingIncome.next()


async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text if message.text != reply_keyboard_texts['skip'][0] else '')
    data = await state.get_data()
    try:
        bot_message = await message.answer(
            text=bot_responses['adding income']['verification of entered data'].format(
                amount=data.get('amount'),
                category=data.get('category'),
                label=data.get('label'),
                date=data.get('date'),
                place=data.get('place'),
                description=data.get('description'),
            ),
            reply_markup=reply_keyboards.create_reply_keyboards(
                reply_keyboard_texts['verification of entered data']
            )
        )
    except aiogram.utils.exceptions.CantParseEntities as error:
        await process_error(error, message, state)
        return
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingIncome.next()


async def process_verification_is_ok(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.add_income(data=data, telegram_user_id=message.chat.id)
    await message.answer(text=bot_responses['adding income']['verification is ok'].format(
            amount=data.get('amount'),
            category=data.get('category'),
            label=data.get('label'),
            date=data.get('date'),
            place=data.get('place'),
            description=data.get('description'),
        ), reply_markup=reply_keyboards.menu)
    await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
    await state.finish()


async def process_verification_is_not_ok(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(text=bot_responses['adding income']['verification is not ok'],
                         reply_markup=reply_keyboards.menu)
    await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
    await state.finish()


def register_handlers_adding_income(dp: Dispatcher):
    dp.register_message_handler(start_reply_adding_income,
                                Text(equals=reply_keyboard_texts['menu']['add income'], ignore_case=True), state='*')
    dp.register_message_handler(process_amount, regexp=r'^\d+[\.,]?\d*$', state=AddingIncome.amount)
    dp.register_message_handler(process_invalid_amount, state=AddingIncome.amount)
    dp.register_message_handler(process_category, state=AddingIncome.category)
    dp.register_message_handler(process_label, state=AddingIncome.label)
    dp.register_message_handler(process_date, state=AddingIncome.date)
    dp.register_message_handler(process_place, state=AddingIncome.place)
    dp.register_message_handler(process_description, state=AddingIncome.description)
    dp.register_message_handler(process_verification_is_ok,
                                Text(equals=reply_keyboard_texts['verification of entered data'][0], ignore_case=True),
                                state=AddingIncome.verification)
    dp.register_message_handler(process_verification_is_not_ok, state=AddingIncome.verification)
