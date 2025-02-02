from aiogram import types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from keyboards import get_main_keyboard, get_cancel_keyboard, get_date_keyboard
from models import P2PTransaction
from config import logger

class TransactionStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_date = State()

async def register_handlers(dp, db_session):
    
    @dp.message(CommandStart())
    async def send_welcome(message: types.Message):
        keyboard = get_main_keyboard()
        await message.reply(
            "👋 Привет! Я помогу тебе отслеживать твои P2P транзакции на Bybit.\n\n"
            "Используй кнопки ниже для управления:",
            reply_markup=keyboard
        )

    @dp.message(F.text == "📊 Статистика")
    async def show_statistics(message: types.Message):
        user_id = message.from_user.id
        
        # Get all transactions for the user
        buys = db_session.query(P2PTransaction).filter_by(
            user_id=user_id,
            transaction_type='buy'
        ).order_by(P2PTransaction.date.desc()).all()
        
        sells = db_session.query(P2PTransaction).filter_by(
            user_id=user_id,
            transaction_type='sell'
        ).order_by(P2PTransaction.date.desc()).all()
        
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

    @dp.message(F.text == "💰 Добавить пополнение")
    async def start_add_deposit(message: types.Message, state: FSMContext):
        await state.set_state(TransactionStates.waiting_for_amount)
        await state.update_data(transaction_type='buy')
        keyboard = get_cancel_keyboard()
        await message.reply(
            "Введите сумму пополнения в рублях:",
            reply_markup=keyboard
        )

    @dp.message(F.text == "💸 Добавить продажу")
    async def start_add_sell(message: types.Message, state: FSMContext):
        await state.set_state(TransactionStates.waiting_for_amount)
        await state.update_data(transaction_type='sell')
        keyboard = get_cancel_keyboard()
        await message.reply(
            "Введите сумму продажи в рублях:",
            reply_markup=keyboard
        )

    @dp.message(F.text == "❌ Отмена")
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
            
            keyboard = get_date_keyboard()
            await message.reply(
                "Введите дату операции в формате ДД.ММ.ГГГГ (например, 25.02.2024)\n"
                "Или нажмите кнопку для использования текущей даты:",
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
            
            # Parse date or use current date if button clicked
            text = message.text.strip() if message.text else ""
            if text == "📅 Использовать текущую дату":
                date = datetime.now()
            else:
                try:
                    date = datetime.strptime(text, "%d.%m.%Y")
                except ValueError:
                    await message.reply(
                        "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например, 25.02.2024)\n"
                        "Или нажмите кнопку для использования текущей даты",
                        reply_markup=get_date_keyboard()
                    )
                    return
            
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