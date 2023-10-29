"""Global configs and constants"""
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
# PostgresSQL config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = os.getenv("DB_URL")
PASSWORD_SUPER_USER = os.getenv("PASSWORD_SUPER_USER")

TIMEZONE = os.getenv("TIMEZONE", "America/Bahia")

DEBUG = os.getenv("DEBUG")

# Logging config.

FORMAT = (
    "[%(asctime)s][%(levelname)s] %(name)s "
    "%(filename)s:%(funcName)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
date_str = datetime.now().strftime("%Y-%m-%d")
LOG_FILENAME = f"{BASE_DIR}/logs/{date_str}.log"

DEFAULT_DATE_FORMAT = "%d/%m/%Y"

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_HOURS = 10
UPLOAD_DIR = os.path.join(BASE_DIR, "contracts")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

PERMISSIONS = {
    "lending": {
        "models": [
            {"name": "asset", "label": "Ativos"},
            {"name": "lending", "label": "Comodato"},
            {"name": "verification", "label": "Verificação de Ativo"},
            {"name": "document", "label": "Documentos"},
            {"name": "mantenance", "label": "Manutenções e Melhorias"},
        ],
        "label": "Comodato",
    },
    "people": {
        "models": [
            {"name": "employee", "label": "Colaboradores"},
        ],
        "label": "Pessoas",
    },
    "auth": {
        "models": [
            {"name": "permission", "label": "Permissões"},
            {"name": "role", "label": "Perfil de usuário"},
            {"name": "user", "label": "Usuários"},
        ],
        "label": "Grupos e Permissões",
    },
    "invoice": {"models": [], "label": "Notas Fiscais"},
    "logs": {
        "models": [
            {
                "name": "log",
                "label": "Logs",
            },
        ],
        "label": "Logs",
    },
}

NOT_ALLOWED = "Não permitido"

PAGE_NUMBER_DESCRIPTION = "Page number"

PAGE_SIZE_DESCRIPTION = "Page size"

PAGINATION_NUMBER = 15

MAX_PAGINATION_NUMBER = 100

ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://datasync-totvs:8001",
]
