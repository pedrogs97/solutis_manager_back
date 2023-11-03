"""Database connection"""
import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config import get_database_url

Engine = create_engine(get_database_url(), pool_pre_ping=True)
Session_db = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=Engine,
)


Base = declarative_base()

logger = logging.getLogger(__name__)
