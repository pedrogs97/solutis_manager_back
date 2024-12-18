"""Global configs and constants"""

import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
# PostgresSQL config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_SERVER = os.getenv("MYSQL_SERVER", "localhost")


def get_database_url(test=False):
    """Return database url"""
    server = DB_SERVER if not test else os.getenv("MYSQL_SERVER_TEST", "localhost")
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
SCHEDULER_ACTIVE = os.getenv("SCHEDULER_ACTIVE")

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
STORAGE_DIR = "storage" if DEBUG else "/storage"
CONTRACT_UPLOAD_DIR = os.path.join(STORAGE_DIR, "contracts")
TERM_UPLOAD_DIR = os.path.join(STORAGE_DIR, "terms")
REPORT_UPLOAD_DIR = os.path.join(STORAGE_DIR, "reports")
ATTACHMENTS_UPLOAD_DIR = os.path.join(STORAGE_DIR, "attachments")
CONTRACT_UPLOAD_TEST_DIR = os.path.join(BASE_DIR, "contracts")
MEDIA_UPLOAD_DIR = os.path.join(STORAGE_DIR, "media")
MEDIA_UPLOAD_TEST_DIR = os.path.join(BASE_DIR, "media")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
TMP_DIR = "tmp"

BASE_API = "/api/v1"

PERMISSIONS = {
    "asset": {
        "models": [
            {"name": "asset", "label": "Ativos"},
            {"name": "asset_type", "label": "Tipos de Ativo"},
            {"name": "asset_status", "label": "Status de Ativo"},
            {"name": "verification", "label": "Verificação de Ativo"},
            {"name": "maintenance", "label": "Manutenções e Melhorias"},
        ],
        "label": "Ativos",
    },
    "lending": {
        "models": [
            {"name": "lending", "label": "Comodato"},
            {"name": "term", "label": "Termo de Responsabilidade"},
            {"name": "document", "label": "Documentos"},
            {"name": "workload", "label": "Lotação"},
            {"name": "witness", "label": "Testemunha"},
        ],
        "label": "Comodato",
    },
    "people": {
        "models": [
            {"name": "employee", "label": "Colaboradores"},
            {"name": "nationality", "label": "Nacionalidades"},
            {"name": "marital_status", "label": "Estado Civil"},
            {"name": "center_cost", "label": "Centro de Custo"},
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
    "report": {
        "models": [
            {
                "name": "report",
                "label": "Relatórios",
            },
        ],
        "label": "Relatórios",
    },
    "inventory": {
        "models": [
            {"name": "inventory", "label": "Inventário"},
        ],
        "label": "Inventário",
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
    "http://172.21.3.225:3000",
    "http://agile.solutis.net.br:3000",
    "http://127.0.0.1",
    "http://localhost",
    "http://172.21.3.225",
    "http://agile.solutis.net.br",
    "http://datasync-totvs:8001",
    "https://localhost:3000",
    "https://127.0.0.1:3000",
    "https://172.21.3.225:3000",
    "https://agile.solutis.net.br:3000",
    "https://127.0.0.1",
    "https://localhost",
    "https://172.21.3.225",
    "https://agile.solutis.net.br",
]

EMAIL_SOLUTIS_365 = "agile@solutis.com.br"
EMAIL_PASSWORD_SOLUTIS_365 = os.getenv("EMAIL_PASSWORD_SOLUTIS_365")
