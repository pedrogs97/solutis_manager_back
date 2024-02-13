"""invoice models"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String
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

    asset: Mapped["AssetModel"] = relationship()
    asset_id: Mapped[int] = Column(ForeignKey("asset.id"), nullable=False)

    deleted_at = Column("deleted_at", Date, nullable=True)

    def __str__(self):
        return f"{self.number}"
