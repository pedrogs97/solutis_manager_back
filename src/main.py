"""Main Service"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.auth.router import auth_router
from src.auth.service import create_initial_data, create_permissions, create_super_user
from src.config import BASE_API, BASE_DIR, DATE_FORMAT, FORMAT, LOG_FILENAME, ORIGINS
from src.database import ExternalDatabase
from src.datasync.router import datasync_router
from src.invoice.router import invoice_router
from src.lending.router import lending_router
from src.log.router import log_router
from src.people.router import people_router

if not os.path.exists(f"{BASE_DIR}/logs/"):
    os.makedirs(f"{BASE_DIR}/logs/")

file_handler = TimedRotatingFileHandler(LOG_FILENAME, when="midnight")
file_handler.suffix = "bkp"
logging.basicConfig(
    encoding="utf-8",
    level=logging.DEBUG,
    format=FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[file_handler],
)
logger = logging.getLogger(__name__)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=f"{BASE_DIR}/src/static"), name="static")

app.include_router(auth_router, prefix=BASE_API)
app.include_router(invoice_router, prefix=BASE_API)
app.include_router(lending_router, prefix=BASE_API)
app.include_router(log_router, prefix=BASE_API)
app.include_router(people_router, prefix=BASE_API)
app.include_router(datasync_router, prefix=BASE_API)


@app.get("/health/", tags=["Service"])
def health_check():
    """Check server up"""
    return True


@app.get("/sqlserver/check/", tags=["Service"])
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


@app.get("/", tags=["Service"])
def root():
    """Redirect to docs"""
    return RedirectResponse(url="/docs")


@app.on_event("startup")
async def startup_base_data():
    """
    Instatialize base user and permissions if does not exist.
    """
    create_super_user()
    create_permissions()
    create_initial_data()
