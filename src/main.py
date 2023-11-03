"""Main Service"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.auth.router import auth_router
from src.auth.service import create_permissions, create_super_user
from src.config import BASE_DIR, DATE_FORMAT, FORMAT, LOG_FILENAME, ORIGINS
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
app.mount(
    "/static", StaticFiles(directory=f"{BASE_DIR}/src/static"), name="static")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(people_router, prefix="/api/v1")


@app.get("/health/", tags=["Service"])
def health_check():
    """Check server up"""
    return True

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
