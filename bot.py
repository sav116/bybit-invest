import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from datetime import datetime
import os
from environs import Env
from models import init_db, P2PTransaction
from keyboards import get_main_keyboard, get_cancel_keyboard
from sqlalchemy import desc

# Load environment variables
env = Env()
env.read_env()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=env("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Initialize database
db_session = init_db(env("DATABASE_URL"))

# Get admin ID from env
ADMIN_ID = env.int("ADMIN_ID")

# States
class TransactionStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_date = State()

async def on_startup():
    """Отправляет сообщение администратору при запуске бота"""
    try:
        await bot.send_message(
            ADMIN_ID,
            "✅ Бот запущен и готов к работе!"
        )
        logger.info(f"Startup notification sent to admin (ID: {ADMIN_ID})")
    except Exception as e:
        logger.error(f"Failed to send startup notification: {e}")

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    keyboard = get_main_keyboard()
    await message.reply(
        "👋 Привет! Я помогу тебе отслеживать твои P2P транзакции на Bybit.\n\n"
        "Используй кнопки ниже для управления:",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.text == "📊 Статистика")
async def show_statistics(message: types.Message):
    user_id = message.from_user.id
    
    # Get all transactions for the user
    buys = db_session.query(P2PTransaction).filter_by(
        user_id=user_id,
        transaction_type='buy'
    ).order_by(desc(P2PTransaction.date)).all()
    
    sells = db_session.query(P2PTransaction).filter_by(
        user_id=user_id,
        transaction_type='sell'
    ).order_by(desc(P2PTransaction.date)).all()
    
    total_bought = sum(t.amount for t in buys)
    total_sold = sum(t.amount for t in sells)
    
    # Формируем основную статистику
    stats = [
        "📊 Статистика ваших P2P транзакций:\n",
        f"💰 Всего внесено: {total_bought:,.2f} ₽",
        f"📈 Всего покупок: {len(buys)}",
        f"💸 Всего продано: {total_sold:,.2f} ₽",
        f"📉 Всего продаж: {len(sells)}\n"
    ]
    
    # Добавляем последние 5 пополнений
    if buys:
        stats.append("\n🔵 Последние пополнения:")
        for t in buys[:5]:
            stats.append(f"• {t.date.strftime('%d.%m.%Y')}: {t.amount:,.2f} ₽")
    
    # Добавляем последние 5 продаж
    if sells:
        stats.append("\n🔴 Последние продажи:")
        for t in sells[:5]:
            stats.append(f"• {t.date.strftime('%d.%m.%Y')}: {t.amount:,.2f} ₽")
    
    keyboard = get_main_keyboard()
    await message.reply("\n".join(stats), reply_markup=keyboard)

@dp.message(lambda message: message.text == "💰 Добавить пополнение")
async def start_add_deposit(message: types.Message, state: FSMContext):
    await state.set_state(TransactionStates.waiting_for_amount)
    await state.update_data(transaction_type='buy')
    keyboard = get_cancel_keyboard()
    await message.reply(
        "Введите сумму пополнения в рублях:",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.text == "💸 Добавить продажу")
async def start_add_sell(message: types.Message, state: FSMContext):
    await state.set_state(TransactionStates.waiting_for_amount)
    await state.update_data(transaction_type='sell')
    keyboard = get_cancel_keyboard()
    await message.reply(
        "Введите сумму продажи в рублях:",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.text == "❌ Отмена")
async def cancel_operation(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    keyboard = get_main_keyboard()
    await message.reply(
        "Операция отменена.",
        reply_markup=keyboard
    )

@dp.message(TransactionStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Save amount to state and ask for date
        await state.update_data(amount=amount)
        await state.set_state(TransactionStates.waiting_for_date)
        
        keyboard = get_cancel_keyboard()
        await message.reply(
            "Введите дату операции в формате ДД.ММ.ГГГГ (например, 25.02.2024)\n"
            "Или нажмите Enter для использования текущей даты:",
            reply_markup=keyboard
        )
        
    except ValueError:
        keyboard = get_cancel_keyboard()
        await message.reply(
            "❌ Пожалуйста, введите корректное число.",
            reply_markup=keyboard
        )

@dp.message(TransactionStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        # Get saved data
        state_data = await state.get_data()
        amount = state_data.get('amount')
        transaction_type = state_data.get('transaction_type')
        
        # Parse date or use current date if empty
        if message.text.strip():
            try:
                date = datetime.strptime(message.text.strip(), "%d.%m.%Y")
            except ValueError:
                await message.reply(
                    "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например, 25.02.2024)",
                    reply_markup=get_cancel_keyboard()
                )
                return
        else:
            date = datetime.now()
        
        # Create and save transaction
        transaction = P2PTransaction(
            user_id=message.from_user.id,
            amount=amount,
            transaction_type=transaction_type,
            date=date
        )
        db_session.add(transaction)
        db_session.commit()
        
        await state.clear()
        
        action_type = "пополнение" if transaction_type == 'buy' else "продажа"
        keyboard = get_main_keyboard()
        await message.reply(
            f"✅ {action_type.capitalize()} на сумму {amount:,.2f} ₽ "
            f"от {date.strftime('%d.%m.%Y')} успешно сохранено!",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error processing date: {e}")
        keyboard = get_main_keyboard()
        await message.reply(
            "❌ Произошла ошибка. Попробуйте снова.",
            reply_markup=keyboard
        )
        await state.clear()

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 