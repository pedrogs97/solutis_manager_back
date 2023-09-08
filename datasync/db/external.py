"""
Database external connection
    - SQLServer Connection
"""
import pyodbc
from datasync.config import CONNECTION_STRING


class ExternalDatabase:
    """Class of SQLServe connection"""

    # Some other example server values are
    # server = 'localhost\sqlexpress' # for a named instance
    # server = 'myserver,port' # to specify an alternate port

    def __init__(self) -> None:
        self.connection = None
        self._cursor = None

    def _try_connect(self) -> None:
        """Try connect with SQLServer database"""
        # ENCRYPT defaults to yes starting in ODBC Driver 18.
        # It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
        if self.connection is None:
            self.connection = pyodbc.connect(CONNECTION_STRING)
        if self._cursor is None:
            self._cursor = self.connection.cursor()
        # (procname [, parameters ])
        # cursor.callproc( )

    def get_connection(self) -> pyodbc.Connection:
        """Return external connection"""
        if self.connection is None:
            self._try_connect()
        return self.connection

    def get_cursor(self) -> pyodbc.Cursor:
        """Return external cursor"""
        if self._cursor is None:
            self._try_connect()
        return self._cursor
