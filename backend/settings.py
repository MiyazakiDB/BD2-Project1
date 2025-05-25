import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

DB_FILE = os.path.join(BASE_DIR, "data", "smart_stock.db")

DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = "uploads"
TABLES_DIR = "tables"

BUFFER_POOL_SIZE = 100
PAGE_SIZE = 4096  # 4KB
