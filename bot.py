import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID, logger, DATABASE_URL
from models import init_db
from handlers import register_handlers

async def on_startup(bot: Bot):
    """Отправляет сообщение администратору при запуске бота"""
    try:
        await bot.send_message(
            ADMIN_ID,
            "✅ Бот запущен и готов к работе!"
        )
        logger.info(f"Startup notification sent to admin (ID: {ADMIN_ID})")
    except Exception as e:
        logger.error(f"Failed to send startup notification: {e}")

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Initialize database
    db_session = init_db(DATABASE_URL)
    
    # Register all handlers
    await register_handlers(dp, db_session)
    
    # Start bot
    await on_startup(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 