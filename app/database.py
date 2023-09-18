"""Database connection"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

Engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session_db = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=Engine,
)

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

logger = logging.getLogger(__name__)
