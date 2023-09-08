"""Sync models"""
from sqlalchemy import Column, Integer, DateTime, func, Float, String
from datasync.models.base import Base


class SyncModel(Base):
    """Sync model"""

    __tablename__ = "syncs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    updated_at = Column("updated_at", DateTime, server_default=func.now())
    count_new_values = Column("count_new_values", Integer, nullable=False)
    model = Column("model", String, nullable=True, default="employee")
    execution_time = Column("execution_time", Float, nullable=False)
