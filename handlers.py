from aiogram import types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from keyboards import (
    get_main_keyboard, get_cancel_keyboard, get_date_keyboard,
    get_transaction_edit_keyboard, get_transaction_type_keyboard,
    get_transactions_list_keyboard
)
from models import P2PTransaction
from config import logger

class TransactionStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_date = State()
    editing_transaction = State()
    editing_amount = State()
    editing_date = State()
    editing_type = State()

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

    @dp.message(F.text == "📝 Редактировать транзакции")
    async def show_transactions_for_edit(message: types.Message):
        user_id = message.from_user.id
        
        # Get all transactions for the user
        transactions = db_session.query(P2PTransaction).filter_by(
            user_id=user_id
        ).order_by(P2PTransaction.date.desc()).all()
        
        if not transactions:
            await message.reply(
                "У вас пока нет транзакций для редактирования.",
                reply_markup=get_main_keyboard()
            )
            return
        
        keyboard = get_transactions_list_keyboard(transactions)
        await message.reply(
            "Выберите транзакцию для редактирования:",
            reply_markup=keyboard
        )

    @dp.callback_query(lambda c: c.data.startswith('edit_'))
    async def edit_transaction(callback_query: types.CallbackQuery, state: FSMContext):
        transaction_id = int(callback_query.data.split('_')[1])
        
        # Get transaction
        transaction = db_session.query(P2PTransaction).filter_by(id=transaction_id).first()
        if not transaction:
            await callback_query.message.reply(
                "❌ Транзакция не найдена.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Save transaction id to state
        await state.update_data(editing_transaction_id=transaction_id)
        await state.set_state(TransactionStates.editing_transaction)
        
        action_type = "пополнение" if transaction.transaction_type == 'buy' else "продажа"
        keyboard = get_transaction_edit_keyboard()
        
        await callback_query.message.reply(
            f"Редактирование транзакции:\n"
            f"Тип: {action_type}\n"
            f"Сумма: {transaction.amount:,.2f} ₽\n"
            f"Дата: {transaction.date.strftime('%d.%m.%Y')}\n\n"
            f"Выберите, что хотите изменить:",
            reply_markup=keyboard
        )
        await callback_query.answer()

    @dp.callback_query(lambda c: c.data == 'cancel_edit')
    async def cancel_edit(callback_query: types.CallbackQuery, state: FSMContext):
        await state.clear()
        await callback_query.message.reply(
            "Редактирование отменено.",
            reply_markup=get_main_keyboard()
        )
        await callback_query.answer()

    @dp.message(TransactionStates.editing_transaction, F.text == "💵 Изменить сумму")
    async def start_edit_amount(message: types.Message, state: FSMContext):
        await state.set_state(TransactionStates.editing_amount)
        keyboard = get_cancel_keyboard()
        await message.reply(
            "Введите новую сумму в рублях:",
            reply_markup=keyboard
        )

    @dp.message(TransactionStates.editing_transaction, F.text == "📅 Изменить дату")
    async def start_edit_date(message: types.Message, state: FSMContext):
        await state.set_state(TransactionStates.editing_date)
        keyboard = get_date_keyboard()
        await message.reply(
            "Введите новую дату в формате ДД.ММ.ГГГГ (например, 25.02.2024)\n"
            "Или нажмите кнопку для использования текущей даты:",
            reply_markup=keyboard
        )

    @dp.message(TransactionStates.editing_transaction, F.text == "🔄 Изменить тип")
    async def start_edit_type(message: types.Message, state: FSMContext):
        await state.set_state(TransactionStates.editing_type)
        keyboard = get_transaction_type_keyboard()
        await message.reply(
            "Выберите новый тип транзакции:",
            reply_markup=keyboard
        )

    @dp.message(TransactionStates.editing_amount)
    async def process_edit_amount(message: types.Message, state: FSMContext):
        try:
            amount = float(message.text.replace(',', '.'))
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            # Get transaction id from state
            state_data = await state.get_data()
            transaction_id = state_data.get('editing_transaction_id')
            
            # Update transaction
            transaction = db_session.query(P2PTransaction).filter_by(id=transaction_id).first()
            if transaction:
                transaction.amount = amount
                db_session.commit()
                
                await state.clear()
                keyboard = get_main_keyboard()
                await message.reply(
                    f"✅ Сумма транзакции успешно изменена на {amount:,.2f} ₽",
                    reply_markup=keyboard
                )
            else:
                raise ValueError("Transaction not found")
            
        except ValueError as e:
            keyboard = get_cancel_keyboard()
            await message.reply(
                "❌ Пожалуйста, введите корректное число.",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing amount: {e}")
            keyboard = get_main_keyboard()
            await message.reply(
                "❌ Произошла ошибка. Попробуйте снова.",
                reply_markup=keyboard
            )
            await state.clear()

    @dp.message(TransactionStates.editing_date)
    async def process_edit_date(message: types.Message, state: FSMContext):
        try:
            # Get transaction id from state
            state_data = await state.get_data()
            transaction_id = state_data.get('editing_transaction_id')
            
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
            
            # Update transaction
            transaction = db_session.query(P2PTransaction).filter_by(id=transaction_id).first()
            if transaction:
                transaction.date = date
                db_session.commit()
                
                await state.clear()
                keyboard = get_main_keyboard()
                await message.reply(
                    f"✅ Дата транзакции успешно изменена на {date.strftime('%d.%m.%Y')}",
                    reply_markup=keyboard
                )
            else:
                raise ValueError("Transaction not found")
            
        except Exception as e:
            logger.error(f"Error editing date: {e}")
            keyboard = get_main_keyboard()
            await message.reply(
                "❌ Произошла ошибка. Попробуйте снова.",
                reply_markup=keyboard
            )
            await state.clear()

    @dp.message(TransactionStates.editing_type)
    async def process_edit_type(message: types.Message, state: FSMContext):
        try:
            # Get transaction id from state
            state_data = await state.get_data()
            transaction_id = state_data.get('editing_transaction_id')
            
            # Determine new type
            if message.text == "💰 Пополнение":
                new_type = 'buy'
            elif message.text == "💸 Продажа":
                new_type = 'sell'
            else:
                await message.reply(
                    "❌ Пожалуйста, выберите тип транзакции, используя кнопки.",
                    reply_markup=get_transaction_type_keyboard()
                )
                return
            
            # Update transaction
            transaction = db_session.query(P2PTransaction).filter_by(id=transaction_id).first()
            if transaction:
                transaction.transaction_type = new_type
                db_session.commit()
                
                await state.clear()
                keyboard = get_main_keyboard()
                action_type = "пополнение" if new_type == 'buy' else "продажу"
                await message.reply(
                    f"✅ Тип транзакции успешно изменен на {action_type}",
                    reply_markup=keyboard
                )
            else:
                raise ValueError("Transaction not found")
            
        except Exception as e:
            logger.error(f"Error editing type: {e}")
            keyboard = get_main_keyboard()
            await message.reply(
                "❌ Произошла ошибка. Попробуйте снова.",
                reply_markup=keyboard
            )
            await state.clear() 