from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="💰 Добавить пополнение")],
        [KeyboardButton(text="💸 Добавить продажу")],
        [KeyboardButton(text="📊 Статистика")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text="❌ Отмена")]]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Нажмите для отмены"
    ) 