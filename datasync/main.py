"""Main Service"""
import logging
from logging.handlers import TimedRotatingFileHandler
from pytz import timezone
from fastapi import FastAPI
from datasync.database import ExternalDatabase
from datasync.config import FORMAT, DATE_FORMAT, LOG_FILENAME, TIMEZONE
from datasync.router import router as fetch_router
from datasync.scheduler import SchedulerService

app = FastAPI()

file_handler = TimedRotatingFileHandler(LOG_FILENAME, when="midnight")
file_handler.suffix = "bkp"
file_handler.formatter = timezone(TIMEZONE)
logging.basicConfig(
    encoding="utf-8",
    level=logging.DEBUG,
    format=FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[file_handler],
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_scheduler():
    """
    Instatialize the Scheduler Service
    This allows for persistent schedules across server restarts.
    """
    SchedulerService().start()


@app.on_event("shutdown")
async def shutdown_scheduler():
    """
    An Attempt at Shutting down the Scheduler Service
    """
    SchedulerService().shutdown()


@app.on_event("shutdown")
async def shutdown_external_db():
    """
    An Attempt at Shutting down open connection ou cursor
    """
    external_db = ExternalDatabase()
    cnxn = external_db.get_connection()
    cursor = external_db.get_cursor()
    if cursor is not None:
        cursor.close()
    if cnxn is not None:
        cnxn.close()


@app.get("/health/check/")
def health_check():
    """Check server up"""
    return True


@app.get("/sqlserver/check/")
def sqlserver_check():
    """Check sqlserver connection"""
    response = "Not connected"
    try:
        external_db = ExternalDatabase()
        cnxn = external_db.get_connection()
        cursor = external_db.get_cursor()
        cursor.execute("SELECT @@version;")
        row = cursor.fetchone()
        while row:
            response = row[0]
            row = cursor.fetchone()
        cursor.close()
        cnxn.close()
        return response
    except AttributeError:
        logger.warning("Unvailable SQLSERVER.")
        return response
    except Exception as err:
        logger.error("Internal error. %s", err.args[1])
        return f"{response}"


app.include_router(fetch_router)
