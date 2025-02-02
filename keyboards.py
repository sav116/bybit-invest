from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="💰 Добавить пополнение")],
        [KeyboardButton(text="💸 Добавить продажу")],
        [KeyboardButton(text="📝 Редактировать транзакции")],
        [KeyboardButton(text="📊 Статистика")]
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    return keyboard

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="❌ Отмена")]]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Нажмите для отмены"
    )
    return keyboard

def get_date_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📅 Использовать текущую дату")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Введите дату или используйте текущую"
    )
    return keyboard

def get_transaction_edit_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="💵 Изменить сумму")],
        [KeyboardButton(text="📅 Изменить дату")],
        [KeyboardButton(text="🔄 Изменить тип")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите что изменить"
    )
    return keyboard

def get_transaction_type_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="💰 Пополнение")],
        [KeyboardButton(text="💸 Продажа")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите тип транзакции"
    )
    return keyboard

def get_transactions_list_keyboard(transactions) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for t in transactions:
        action = "пополнение" if t.transaction_type == 'buy' else "продажа"
        button_text = f"{t.date.strftime('%d.%m.%Y')} - {action} {t.amount:,.2f} ₽"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"edit_{t.id}")
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")
    ])
    
    return keyboard 