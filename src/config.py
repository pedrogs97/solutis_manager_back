"""Global configs and constants"""
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
# PostgresSQL config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_database_url(test=False):
    """Return database url"""
    server = (
        os.getenv("MYSQL_SERVER", "localhost")
        if not test
        else os.getenv("MYSQL_SERVER_TEST", "localhost")
    )
    db = os.getenv("MYSQL_DATABASE", "app") if not test else "db_test"
    user = (
        os.getenv("MYSQL_USER", "root")
        if not test
        else os.getenv("MYSQL_USER_TEST", "root")
    )
    password = (
        os.getenv("MYSQL_PASSWORD", "")
        if not test
        else os.getenv("MYSQL_PASSWORD_TEST", "")
    )
    port = os.getenv("MYSQL_PORT", "3306")
    return f"mysql+mysqlconnector://{user}:{password}@{server}:{port}/{db}"


def get_database_server_url():
    """Return database server url"""
    server = os.getenv("MYSQL_SERVER_TEST", "localhost")
    user = os.getenv("MYSQL_USER_TEST", "root")
    password = os.getenv("MYSQL_PASSWORD_TEST", "")
    return f"mysql+mysqlconnector://{user}:{password}@{server}"


SQLSERVE_HOST_DB = os.environ.get("SQLSERVE_HOST_DB", "")
SQLSERVE_NAME_DB = os.environ.get("SQLSERVE_NAME_DB", "")
SQLSERVE_USER_DB = os.environ.get("SQLSERVE_USER_DB", "")
SQLSERVE_PASSWORD_DB = os.environ.get("SQLSERVE_PASSWORD_DB", "")

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
DEFAULT_DATE_TIME_FORMAT = "%d/%m/%Y %H:%M:%S"

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_HOURS = 8
REFRESH_TOKEN_EXPIRE_DAYS = 2
CONTRACT_UPLOAD_DIR = os.path.join(BASE_DIR, "contracts")

MEDIA_UPLOAD_DIR = os.path.join(BASE_DIR, "media")

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

BASE_API = "/api/v1"

PERMISSIONS = {
    "lending": {
        "models": [
            {"name": "asset", "label": "Ativos"},
            {"name": "asset_type", "label": "Tipos de Ativo"},
            {"name": "asset_status", "label": "Status de Ativo"},
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
            {"name": "nationality", "label": "Nacionalidades"},
            {"name": "matrial_status", "label": "Estado Civil"},
            {"name": "gender", "label": "Generos"},
            {"name": "role", "label": "Cargos"},
        ],
        "label": "Pessoas",
    },
    "auth": {
        "models": [
            {"name": "permission", "label": "Permissões"},
            {"name": "group", "label": "Perfil de usuário"},
            {"name": "user", "label": "Usuários"},
        ],
        "label": "Grupos e Permissões",
    },
    "invoice": {
        "models": [{"name": "invoice", "label": "Nota Fiscal"}],
        "label": "Notas Fiscais",
    },
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
