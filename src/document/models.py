"""Lending models"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from src.database import Base


class DocumentTypeModel(Base):
    """
    Document type model

    * Contrato
    * Termo de reponsabilidade
    * Distrato
    * Distrato de Termo de reponsabilidade
    """

    __tablename__ = "document_type"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=40), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class DocumentModel(Base):
    """Document model"""

    __tablename__ = "document"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    doc_type: Mapped[DocumentTypeModel] = relationship()
    doc_type_id = Column("doc_type_id", ForeignKey("document_type.id"), nullable=True)

    # caminho do arquivo
    path = Column("path", String(length=255), nullable=True)
    file_name = Column("file_name", String(length=100), nullable=False)
    deleted = Column("deleted", Boolean, default=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.file_name}"
