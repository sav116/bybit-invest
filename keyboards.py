from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="💰 Добавить пополнение")],
        [KeyboardButton(text="💸 Добавить продажу")],
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