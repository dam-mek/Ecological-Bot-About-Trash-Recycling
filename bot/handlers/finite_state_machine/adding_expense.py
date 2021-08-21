from datetime import date

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


class AddingExpense(StatesGroup):
    amount = State()
    category = State()
    date = State()
    label = State()
    place = State()
    description = State()
    verification = State()
    message_ids = State()


async def navigate_category_state():
    return 'ok'


async def navigate_date_state(a, b):
    return 'ok'


async def navigate_state(message: types.Message, state: FSMContext) -> types.Message:
    print(state.get_state())
    if state.get_state() == 'date':
        client_settings = await db.get_client_settings(message.chat.id)
        if client_settings.asking_label:
            await AddingExpense.label.set()
            return await message.answer(text=bot_responses['adding expense']['label'],
                                        reply_markup=reply_keyboards.get_label_reply_keyboard(message.chat.id))
        if client_settings.asking_place:
            await AddingExpense.place.set()
            return await message.answer(text=bot_responses['adding expense']['place'],
                                        reply_markup=reply_keyboards.places)
        if client_settings.asking_description:
            await AddingExpense.description.set()
            return await message.answer(text=bot_responses['adding expense']['description'],
                                        reply_markup=reply_keyboards.description)


async def start_reply_adding_expense(message: types.Message, state: FSMContext):
    bot_message = await message.answer(text=bot_responses['adding expense']['amount'],
                                       reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(message_ids=[message.message_id, bot_message.message_id])
    await AddingExpense.amount.set()


async def process_amount(message: types.Message, state: FSMContext):
    try:
        await state.update_data(amount=float(message.text.replace(',', '.')))
    except ValueError as error:
        await process_error(error, message, state)
        return
    bot_message = await message.answer(text=bot_responses['adding expense']['category'],
                                       reply_markup=reply_keyboards.get_category_reply_keyboard(message.chat.id))
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingExpense.next()


async def process_invalid_amount(message: types.Message, state: FSMContext):
    bot_message = await message.answer(text=bot_responses['adding expense']['invalid amount'],
                                       reply_markup=types.ReplyKeyboardRemove())
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])


async def process_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    bot_message = await message.answer(text=bot_responses['adding expense']['date'],
                                       reply_markup=reply_keyboards.dates)
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingExpense.next()


async def process_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    bot_message = await navigate_date_state(message, state)
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])


async def process_label(message: types.Message, state: FSMContext):
    await state.update_data(label=message.text)
    bot_message = await message.answer(text=bot_responses['adding expense']['date'],
                                       reply_markup=reply_keyboards.dates)
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingExpense.next()


async def process_place(message: types.Message, state: FSMContext):
    await state.update_data(place=message.text)
    bot_message = await message.answer(text=bot_responses['adding expense']['description'],
                                       reply_markup=reply_keyboards.description)
    data = await state.get_data()
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingExpense.next()


async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text if message.text != reply_keyboard_texts['skip'][0] else '')
    data = await state.get_data()
    try:
        bot_message = await message.answer(
            text=bot_responses['adding expense']['verification of entered data'].format(
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
    except CantParseEntities as error:
        await process_error(error, message, state)
        return
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await AddingExpense.next()


async def process_verification_is_ok(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.add_expense(
        telegram_user_id=message.chat.id,
        amount=data['amount'],
        category_name=data['category'],
        created_date=data['date'],
        label=data['label'],
        place=data['place'],
        description=data['description'],
    )
    await message.answer(
        text=bot_responses['adding expense']['verification is ok'].format(**data),
        reply_markup=reply_keyboards.menu
    )
    await delete_messages(message.chat.id, data.get('message_ids', []) + [message.message_id])
    await state.finish()


async def process_verification_is_not_ok(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(text=bot_responses['adding expense']['verification is not ok'],
                         reply_markup=reply_keyboards.menu)
    await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
    await state.finish()


def register_handlers_adding_expense(dp: Dispatcher):
    dp.register_message_handler(start_reply_adding_expense,
                                Text(equals=reply_keyboard_texts['menu']['add expense'], ignore_case=True), state='*')
    dp.register_message_handler(process_amount, regexp=r'^\d+[\.,]?\d*$', state=AddingExpense.amount)
    dp.register_message_handler(process_invalid_amount, state=AddingExpense.amount)
    dp.register_message_handler(process_category, state=AddingExpense.category)
    dp.register_message_handler(process_date, state=AddingExpense.date)
    dp.register_message_handler(process_label, state=AddingExpense.label)
    dp.register_message_handler(process_place, state=AddingExpense.place)
    dp.register_message_handler(process_description, state=AddingExpense.description)
    dp.register_message_handler(process_verification_is_ok,
                                Text(equals=reply_keyboard_texts['verification of entered data'][0], ignore_case=True),
                                state=AddingExpense.verification)
    dp.register_message_handler(process_verification_is_not_ok, state=AddingExpense.verification)
