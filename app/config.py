"""Global configs and constants"""
import os
from datetime import datetime

# PostgresSQL config

DATABASE_URL = os.environ.setdefault("DB_URL", "")
PASSWORD_SUPER_USER = os.environ.setdefault("PASSWORD_SUPER_USER", "admin@123")

TIMEZONE = os.environ.setdefault("TIMEZONE", "America/Bahia")

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
    "lending": {
        "models": [
            {"name": "asset", "label": "Ativo"},
            {"name": "lending", "label": "Contrato de Comodato"},
            {"name": "mantenance", "label": "Manutenção"},
        ],
        "label": "Comodato",
    },
    "people": {"models": [{"name": "user", "label": "Usuário"}], "label": "Pesosas"},
    "auth": {
        "models": [
            {"name": "permission", "label": "Permissões"},
            {"name": "role", "label": "Perfil de usuário"},
        ],
        "label": "Grupos e Permissões",
    },
    "invoice": {"models": [], "label": "Nota Fiscal"},
    "logs": {"models": [], "label": "Log"},
}

NOT_ALLOWED = "Not allowed"

PAGE_NUMBER_DESCRIPTION = "Page number"

PAGE_SIZE_DESCRIPTION = "Page size"

PAGINATION_NUMBER = 15

MAX_PAGINATION_NUMBER = 100

ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://datasync-totvs:8001"
]
