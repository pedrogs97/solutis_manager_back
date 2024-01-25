"""Main Service"""
import logging
import os
from contextlib import asynccontextmanager

from apscheduler.jobstores.base import ConflictingIdError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import exc, text
from sqlalchemy.orm import Session

from src.asset.router import asset_router
from src.auth.router import auth_router
from src.auth.service import create_initial_data, create_permissions, create_super_user
from src.backends import get_db_session
from src.config import (  # DATE_FORMAT,; FORMAT,; LOG_FILENAME,
    BASE_API,
    BASE_DIR,
    DB_SERVER,
    ORIGINS,
    SCHEDULER_ACTIVE,
)
from src.database import ExternalDatabase, get_database_url
from src.datasync.router import datasync_router
from src.datasync.scheduler import SchedulerService
from src.exceptions import default_response_exception
from src.invoice.router import invoice_router
from src.lending.router import lending_router
from src.log.router import log_router
from src.maintenance.router import maintenance_router
from src.people.router import people_router
from src.verification.router import verification_router

# from logging.handlers import TimedRotatingFileHandler


if not os.path.exists(f"{BASE_DIR}/logs/"):
    os.makedirs(f"{BASE_DIR}/logs/")

# file_handler = TimedRotatingFileHandler(LOG_FILENAME, when="midnight")
# file_handler.suffix = "bkp"
# logging.basicConfig(
#     encoding="utf-8",
#     level=logging.DEBUG,
#     format=FORMAT,
#     datefmt=DATE_FORMAT,
#     handlers=[file_handler],
# )
logger = logging.getLogger(__name__)

exception_handlers = {
    500: default_response_exception,
    404: default_response_exception,
    401: default_response_exception,
    400: default_response_exception,
}


def read_totvs_db():
    """Excute procedure to retrive TOVTS data"""
    scheduler_service = SchedulerService()
    scheduler_service.read_totvs_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifesapn app"""
    logger.info("Service Version %s", app.version)
    create_permissions()
    create_super_user()
    create_initial_data()
    jobstores = {"default": SQLAlchemyJobStore(url=get_database_url())}
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
    )
    logger.info("Current jobs %s", scheduler.get_jobs())
    try:
        trigger = "cron"
        hour = "12-18"
        minute = "00"
        week = "mon-fri"
        # -- configuração de prod/homol - roda todos os dias as 12:00 e 18:00
        scheduler.add_job(
            read_totvs_db,
            trigger,
            id="datasync",
            day_of_week=week,
            hour=hour,
            minute=minute,
            # Using max_instances=1 guarantees that only one job
            # runs at the same time (in this event loop).
            max_instances=1,
            replace_existing=True,
        )
    except ConflictingIdError:
        logger.info("Job alredy exist")

    if SCHEDULER_ACTIVE:
        scheduler.start()
    # scheduler.schedule_job()
    yield
    # shutdown scheduler
    logging.info("Start shutdown")
    scheduler.remove_job("datasync")
    scheduler.shutdown()
    # close external database
    external_db = ExternalDatabase()
    cnxn = external_db.get_connection()
    cursor = external_db.get_cursor()
    if cursor is not None:
        cursor.close()
    if cnxn is not None:
        cnxn.close()


appAPI = FastAPI(
    exception_handlers=exception_handlers, lifespan=lifespan, version="1.0.3"
)


appAPI.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
appAPI.mount("/static", StaticFiles(directory=f"{BASE_DIR}/src/static"), name="static")

appAPI.include_router(auth_router, prefix=BASE_API)
appAPI.include_router(invoice_router, prefix=BASE_API)
appAPI.include_router(lending_router, prefix=BASE_API)
appAPI.include_router(log_router, prefix=BASE_API)
appAPI.include_router(people_router, prefix=BASE_API)
appAPI.include_router(datasync_router, prefix=BASE_API)
appAPI.include_router(asset_router, prefix=BASE_API)
appAPI.include_router(maintenance_router, prefix=BASE_API)
appAPI.include_router(verification_router, prefix=BASE_API)


@appAPI.get("/health/", tags=["Service"])
def health_check(db_session: Session = Depends(get_db_session)):
    """Check server up"""
    response = {"status": "ok"}
    try:
        result = db_session.execute(text("SELECT VERSION()"))
        version = result.fetchall()[0][0]
        db_session.close_all()
        response.update({"database": {"version": version, "server": DB_SERVER}})
    except exc.TimeoutError:
        response.update({"status": "not ok", "info": "Database disconnected"})
    return response


@appAPI.get("/sqlserver/check/", tags=["Service"])
def sqlserver_check():
    """Check sqlserver connection"""
    response = "Not connected"
    try:
        external_db = ExternalDatabase()
        cnxn = external_db.get_connection(as_dict=False)
        cursor = external_db.get_cursor(as_dict=False)
        cursor.execute("SELECT @@version;")
        row = cursor.fetchone()
        while row:
            response = row[0]
            row = cursor.fetchone()
        cnxn.close()
        return response
    except AttributeError:
        logger.warning("Unvailable SQLSERVER.")
        return response
    except Exception as err:
        logger.error("Internal error. %s", err.args[1])
        return f"{response}"


@appAPI.get("/", tags=["Service"])
def root():
    """Redirect to docs"""
    return RedirectResponse(url="/docs")
