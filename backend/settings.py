import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Database Settings
DB_FILE = os.path.join(BASE_DIR, "data", "smart_stock.db")

# Storage Settings
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = "uploads"
TABLES_DIR = "tables"

# Buffer Pool Settings
BUFFER_POOL_SIZE = 100
PAGE_SIZE = 4096  # 4KB
