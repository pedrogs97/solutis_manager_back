"""invoice models"""

from typing import List

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from src.database import Base


class InvoiceAssets(Base):
    """Invoice asset pivot table"""

    __tablename__ = "invoice_assets"

    asset: Mapped["AssetModel"] = relationship()
    asset_id: Mapped[int] = Column(ForeignKey("asset.id"), primary_key=True)

    invoice: Mapped["InvoiceModel"] = relationship(viewonly=True)
    invoice_id: Mapped[int] = Column(ForeignKey("invoices.id"))
    quantity = Column("quantity", Integer, nullable=False)
    unit_value = Column("unit_value", Float, nullable=False)


class InvoiceModel(Base):
    """Invoice model"""

    __tablename__ = "invoices"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    number = Column("number", String(length=11), nullable=False)
    total_value = Column("total_value", Float, nullable=False)
    total_quantity = Column("total_quantity", Integer, nullable=False)

    # caminho do arquivo
    path = Column("path", String(length=255), nullable=True)
    file_name = Column("file_name", String(length=100), nullable=True)

    assets: Mapped[List[InvoiceAssets]] = relationship(viewonly=True)

    def __str__(self):
        return f"{self.number}"
