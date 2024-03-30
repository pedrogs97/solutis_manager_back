"""Database connection"""

import logging

import pymssql
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.config import (
    SQLSERVE_HOST_DB,
    SQLSERVE_NAME_DB,
    SQLSERVE_PASSWORD_DB,
    SQLSERVE_USER_DB,
    get_database_url,
)

Engine = create_engine(
    get_database_url(), poolclass=NullPool, pool_pre_ping=True, pool_recycle=60
)
Session_db = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=Engine,
)


Base = declarative_base()

logger = logging.getLogger(__name__)


class ExternalDatabase:
    """Class of SQLServe connection"""

    # Some other example server values are
    # server = 'localhost\sqlexpress' # for a named instance
    # server = 'myserver,port' # to specify an alternate port

    def __init__(self) -> None:
        self.connection = None
        self._cursor = None

    def _try_connect(self, as_dict=True) -> None:
        """Try connect with SQLServer database"""
        # ENCRYPT defaults to yes starting in ODBC Driver 18.
        # It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
        if self.connection is None:
            # pylint: disable=no-member
            self.connection = pymssql.connect(
                server=SQLSERVE_HOST_DB,
                user=SQLSERVE_USER_DB,
                password=SQLSERVE_PASSWORD_DB,
                database=SQLSERVE_NAME_DB,
            )
        if self._cursor is None:
            self._cursor = self.connection.cursor(as_dict)

    def get_connection(self, as_dict=True):
        """Return external connection"""
        if self.connection is None:
            self._try_connect(as_dict)
        return self.connection

    def get_cursor(self, as_dict=True):
        """Return external cursor"""
        if self._cursor is None:
            self._try_connect(as_dict)
        return self._cursor
