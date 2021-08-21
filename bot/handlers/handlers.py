from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from bot.reply_keyboards import reply_keyboard_texts
from bot import reply_keyboards
from bot import expenses
from bot import exceptions
from bot.handlers.finite_state_machine.buying import register_handlers_buying
from bot.handlers.finite_state_machine.adding_eballs import register_handlers_adding_eballs
from bot.handlers.finite_state_machine.adding_product import register_handlers_adding_product
from bot.messages import bot_responses
from bot.middlewares import check_is_master
import db.clients


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(send_start_master, check_is_master, commands=['start'], state='*')
    register_handlers_adding_eballs(dp)
    register_handlers_adding_product(dp)
    dp.register_message_handler(future_master, Text(equals=reply_keyboard_texts['menu master']['add master']), check_is_master, state='*')
    dp.register_message_handler(send_start_master, check_is_master, state='*')
    dp.register_message_handler(send_start, commands=['start'], state='*')
    dp.register_message_handler(send_balance,
                                Text(equals=reply_keyboard_texts['menu slave']['Balance'], ignore_case=True))
    dp.register_message_handler(send_statistic,
                                Text(equals=reply_keyboard_texts['menu slave']['Statistic'], ignore_case=True))
    dp.register_message_handler(send_telegram_id,
                                Text(equals=reply_keyboard_texts['menu slave']['Telegram Id'], ignore_case=True))
    register_handlers_buying(dp)
    # register_handlers_adding_income(dp)
    # dp.register_message_handler(settings, Text(equals=reply_keyboard_texts['menu']['settings'], ignore_case=True))
    dp.register_message_handler(del_expense, lambda message: message.text.startswith('/del'))
    dp.register_message_handler(categories_list, commands=['categories'])
    dp.register_message_handler(today_statistics, commands=['today'])
    dp.register_message_handler(month_statistics, commands=['month'])
    dp.register_message_handler(list_expenses, commands=['expenses'])
    dp.register_message_handler(feedback_message, commands=['feedback'])
    dp.register_message_handler(send_start)
    dp.register_message_handler(add_expense)


async def send_start(message: types.Message):
    db.clients.add_new_client(message.from_user.id)
    await message.answer(text=bot_responses['start'], reply_markup=reply_keyboards.menu_slave)


async def send_start_master(message: types.Message):
    await message.answer(text='You are master', reply_markup=reply_keyboards.menu_master)


async def future_master(message: types.Message):
    await message.answer(text='Это в будущем будем создано...', reply_markup=reply_keyboards.menu_master)


async def send_statistic(message: types.Message, state: FSMContext):
    txt = 'Вся история мусора, сданного вами в переработку:\n\n'
    for trash in db.clients.get_all_taken_trashes(message.from_user.id):
        txt += f'{trash[0].icon}{trash[0].name}{trash[0].icon} — {trash[1]} г.\n'
    await message.answer(txt, reply_markup=reply_keyboards.menu_slave)


async def send_balance(message: types.Message, state: FSMContext):
    balance = db.clients.get_eballs(message.from_user.id)
    await message.answer(f'Ваша количество баллов: {balance}', reply_markup=reply_keyboards.menu_slave)


async def send_telegram_id(message: types.Message):
    await message.answer(f"Ваш код — <b>{message.from_user.id}</b>\nЕго надо сообщить кОмУ-То", reply_markup=reply_keyboards.menu_slave)


async def cancel_handler(message: types.Message, state: FSMContext):
    """Allow user to cancel any action"""

    current_state = await state.get_state()
    if current_state is None:
        await message.answer(bot_responses['cancel handler']['no state'], reply_markup=reply_keyboards.menu)
        return

    # logging.info('Cancelling state %r', current_state)
    await state.finish()
    await message.answer(bot_responses['cancel handler']['state was cleared'], reply_markup=reply_keyboards.menu)


async def del_expense(message: types.Message):
    """Удаляет одну запись о расходе по её идентификатору"""
    row_id = int(message.text[4:])
    expenses.delete_expense(row_id)
    answer_message = 'Удалил'
    await message.answer(answer_message)


async def categories_list(message: types.Message):
    """Sends a list of expense categories"""
    categories = Categories(int(message.chat.id)).get_all_categories()
    answer_text = 'Категории трат:\n\n'
    for category in categories:
        answer_text += f'{category.icon} {category.name.capitalize()}\n'
    await message.answer(answer_text)


async def today_statistics(message: types.Message):
    """Отправляет сегодняшнюю статистику трат"""
    answer_message = expenses.get_today_statistics()
    await message.answer(answer_message)


async def month_statistics(message: types.Message):
    """Отправляет статистику трат текущего месяца"""
    answer_message = expenses.get_month_statistics()
    await message.answer(answer_message)


async def list_expenses(message: types.Message):
    """Отправляет последние несколько записей о расходах"""
    last_expenses = expenses.last()
    if not last_expenses:
        await message.answer('Расходы ещё не заведены')
        return

    last_expenses_rows = [
        f'{expense.amount} руб. на {expense.category_name} — нажми '
        f'/del{expense.id} для удаления'
        for expense in last_expenses]
    answer_message = 'Последние сохранённые траты:\n\n* ' + '\n\n* ' \
        .join(last_expenses_rows)
    await message.answer(answer_message)


async def add_expense(message: types.Message):
    """Добавляет новый расход"""
    try:
        expense = expenses.add_expense(message.text)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f'Добавлены траты {expense.amount} руб на {expense.category_name}.\n\n'
        f'{expenses.get_today_statistics()}')
    await message.answer(answer_message)


async def feedback_message(message: types.Message):
    await message.answer(bot_responses['feedback'])
