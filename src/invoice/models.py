"""invoice models"""
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from src.database import Base

invoice_assets = Table(
    "invoice_assets",
    Base.metadata,
    Column("invoice_id", ForeignKey("invoices.id"), primary_key=True),
    Column("asset_id", ForeignKey("asset.id"), primary_key=True),
)


class InvoiceModel(Base):
    """Invoice model"""

    __tablename__ = "invoices"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    number = Column("number", String(length=11), nullable=False)
    total_value = Column("total_value", Float, nullable=False)
    total_quantity = Column("total_quantity", Integer, nullable=False)

    # caminho do arquivo
    path = Column("path", String(length=255), nullable=True)
    file_name = Column("file_name", String(length=100), nullable=False)

    assets = relationship(
        "AssetModel", secondary=invoice_assets, back_populates="invoices"
    )

    def __str__(self):
        return f"{self.number}"
