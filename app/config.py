"""Global configs and constants"""
import os
from datetime import datetime

# PostgresSQL config

DATABASE_URL = os.environ.setdefault("DB_URL", "")
PASSWORD_SUPER_USER = os.environ.setdefault("PASSWORD_SUPER_USER", "admin@123")

# Logging config.

FORMAT = (
    "[%(asctime)s][%(levelname)s] %(name)s "
    "%(filename)s:%(funcName)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
date_str = datetime.now().strftime("%Y-%m-%d")
LOG_FILENAME = f"./logs/{date_str}.log"

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_HOURS = 10

PERMISSIONS = {
    "lending": ["asset", "lending", "mantenance"],
    "people": [],
    "auth": ["user", "permission", "role"],
    "invoice": [],
    "logs": [],
}
