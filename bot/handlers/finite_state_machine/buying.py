from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

import db.places
import db.products
import db.categories
from bot import reply_keyboards
from bot.handlers.utils import delete_messages
from bot.messages import bot_responses
from bot.reply_keyboards import reply_keyboard_texts


class BuyProduct(StatesGroup):
    product = State()
    place = State()
    verification = State()
    message_ids = State()


async def start_reply_buying(message: types.Message, state: FSMContext):
    products = db.products.get_products()
    response_text = bot_responses['products']['introduction']
    list_for_reply_keyboard = []
    for product in products:
        response_text += bot_responses['products']['row in list'].format(product_name=product.name,
                                                                         price=product.price) + '\n'
        list_for_reply_keyboard += [f'Купить {product.name}']
    list_for_reply_keyboard += ['Выйти']
    bot_message = await message.answer(text=response_text,
                                       reply_markup=reply_keyboards.create_reply_keyboards(list_for_reply_keyboard))
    await state.update_data(message_ids=[message.message_id, bot_message.message_id])
    await BuyProduct.product.set()


async def process_product(message: types.Message, state: FSMContext):
    text = message.text.replace('Купить ', '')
    data = await state.get_data()

    if text == 'Выйти':
        bot_message = await message.answer(text='Операция отменена',
                                           reply_markup=reply_keyboards.menu_slave)
        await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
        await state.finish()
        return
    if text not in map(lambda p: p.name, db.products.get_products()) and data.get('product') is None:
        bot_message = await message.answer(text='Несуществуещий товар, выберите снова')

        await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
        await start_reply_buying(message, state)
        return
    bot_message = await message.answer(text='Выберите место доставки',
                                       reply_markup=reply_keyboards.create_reply_keyboards(
                                           list(map(lambda x: x.address, db.places.get_places())) + ['Выйти']))
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await state.update_data(product=text)
    await BuyProduct.place.set()


async def process_place(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == 'Выйти':
        bot_message = await message.answer(text='Операция отменена',
                                           reply_markup=reply_keyboards.menu_slave)
        await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
        await state.finish()
        return
    if message.text not in map(lambda x: x.address, db.places.get_places()):
        bot_message = await message.answer(text='Несуществуещее место, выберите снова')
        await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
        await process_product(message, state)
        return
    txt = f"Информация верная?\n{data['product']} заберёте здесь: {message.text}"
    bot_message = await message.answer(text=txt,
                                       reply_markup=reply_keyboards.verification)
    await state.update_data(message_ids=data['message_ids'] + [message.message_id, bot_message.message_id])
    await state.update_data(place=message.text)
    await BuyProduct.verification.set()


async def process_verification(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == 'Да':
        db.products.add_bought_product(message.from_user.id, data['product'], data['place'])
        bot_message = await message.answer(text=f"Ваш товар {data['product']} будет доставлен сюда: {data['place']}",
                                           reply_markup=reply_keyboards.menu_slave)
        db.categories.minus_eballs(message.from_user.id, data['product'])
        await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
        await state.finish()
        return
    bot_message = await message.answer(text='Операция отменена',
                                       reply_markup=reply_keyboards.menu_slave)
    await delete_messages(message.chat.id, data['message_ids'] + [message.message_id])
    await state.finish()


def register_handlers_buying(dp: Dispatcher):
    dp.register_message_handler(start_reply_buying,
                                Text(equals=reply_keyboard_texts['menu slave']['Catalog'], ignore_case=True), state='*')
    dp.register_message_handler(process_product, state=BuyProduct.product)
    dp.register_message_handler(process_place, state=BuyProduct.place)
    dp.register_message_handler(process_verification, state=BuyProduct.verification)
