from environs import Env
import logging
import os

# Load environment variables
env = Env()
env.read_env()

# Bot token
BOT_TOKEN = env("BOT_TOKEN")

# Admin ID
ADMIN_ID = env.int("ADMIN_ID")

# Database URL
# Используем абсолютный путь для базы данных
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'db.sqlite3')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 