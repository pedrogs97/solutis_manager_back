"""Main Service"""
import logging
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI
from app.config import FORMAT, DATE_FORMAT, LOG_FILENAME
from app.auth.service import create_super_user, create_permissions
from app.auth.router import auth_router
from app.people.router import people_router

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

app.include_router(auth_router, prefix="/api/v1")
app.include_router(people_router, prefix="/api/v1")


@app.get("/health/", tags=["Service"])
def health_check():
    """Check server up"""
    return True


@app.on_event("startup")
async def startup_base_data():
    """
    Instatialize base user and permissions if does not exist.
    """
    create_super_user()
    create_permissions()
