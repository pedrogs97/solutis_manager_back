"""Log models"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from src.auth.models import UserModel
from src.database import Base


class LogModel(Base):
    """Log model"""

    __tablename__ = "logs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    user: Mapped[UserModel] = relationship()
    user_id = Column("user_id", ForeignKey(UserModel.id), nullable=False)

    module = Column("module", String(length=100), nullable=False)
    model = Column("model", String(length=100), nullable=False)
    operation = Column("operation", String(length=100), nullable=False)
    identifier = Column("identifier", Integer, nullable=False)
    logged_in = Column("logged_in", DateTime, nullable=False, server_default=func.now())

    def __str__(self):
        date_str = self.logged_in.strftime("%d/%m/%Y")
        return f"{self.module}:{self.operation} - {date_str}"
