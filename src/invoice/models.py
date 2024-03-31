"""invoice models"""

from typing import List

from sqlalchemy import Column, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from src.database import Base


class InvoiceModel(Base):
    """Invoice model"""

    __tablename__ = "invoices"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    number = Column("number", String(length=11), nullable=False)

    # caminho do arquivo
    path = Column("path", String(length=255), nullable=True)
    file_name = Column("file_name", String(length=100), nullable=True)

    assets: Mapped[List["AssetModel"]] = relationship(back_populates="invoice")

    deleted_at = Column("deleted_at", Date, nullable=True)
    created_at = Column(
        "created_at", DateTime, nullable=False, server_default=func.now()
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    def __str__(self):
        return f"{self.number}"
