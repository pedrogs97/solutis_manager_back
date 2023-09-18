"""Global configs and constants"""
import os
from datetime import datetime

# PostgresSQL config

DATABASE_URL = os.environ.setdefault("DB_URL_DATASYNC", "")


# SQLServer configs

HOST_DB = os.environ.setdefault("SQLSERVE_HOST_DB", "")
NAME_DB = os.environ.setdefault("SQLSERVE_NAME_DB", "")
USER_DB = os.environ.setdefault("SQLSERVE_USER_DB", "")
PASSWORD_DB = os.environ.setdefault("SQLSERVE_PASSWORD_DB", "")

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
    + HOST_DB
    + ";DATABASE="
    + NAME_DB
    + ";ENCRYPT=yes;UID="
    + USER_DB
    + ";PWD="
    + PASSWORD_DB
    + ";TrustServerCertificate=yes"
)

# Logging config.

FORMAT = (
    "[%(asctime)s][%(levelname)s] %(name)s "
    "%(filename)s:%(funcName)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
date_str = datetime.now().strftime("%Y-%m-%d")
LOG_FILENAME = f"./logs/{date_str}.log"
