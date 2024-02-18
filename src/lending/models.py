"""Lending models"""

from typing import List

from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from src.asset.models import AssetModel
from src.database import Base
from src.datasync.models import CostCenterTOTVSModel
from src.people.models import EmployeeModel


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

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.file_name}"


class WorkloadModel(Base):
    """
    Worload type model
    * Híbrido
    * Home Office
    * Presencial
    """

    __tablename__ = "workload"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=12), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class LendingTypeModel(Base):
    """
    Lending type model

    * Contrato
    * Termo de reponsabilidade
    """

    __tablename__ = "lending_type"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=40), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class LendingStatusModel(Base):
    """
    Lending status model

    * Arquivo pendente
    * Ativo
    * Arquivo de distrato pendente
    * Inativo
    """

    __tablename__ = "lending_status"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=40), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class LendingModel(Base):
    """Lending model"""

    __tablename__ = "lending"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    employee: Mapped[EmployeeModel] = relationship()
    employee_id = Column("employee_id", ForeignKey(EmployeeModel.id), nullable=False)

    asset: Mapped[AssetModel] = relationship()
    asset_id = Column("asset_id", ForeignKey(AssetModel.id), nullable=False)

    document_id = Column("document_id", ForeignKey(DocumentModel.id), nullable=True)
    document: Mapped[DocumentModel] = relationship(foreign_keys=[document_id])

    document_revoke_id = Column(
        "document_revoke_id", ForeignKey(DocumentModel.id), nullable=True
    )
    document_revoke: Mapped[DocumentModel] = relationship(
        foreign_keys=[document_revoke_id]
    )
    # lotação
    workload: Mapped[WorkloadModel] = relationship()
    workload_id = Column("workload_id", ForeignKey(WorkloadModel.id), nullable=True)

    type: Mapped[LendingTypeModel] = relationship()
    type_id = Column(
        "type_id", ForeignKey(LendingTypeModel.id), nullable=False, default=1
    )

    status: Mapped[LendingStatusModel] = relationship()
    status_id = Column("status_id", ForeignKey(LendingStatusModel.id), nullable=True)

    witnesses: Mapped[List["WitnessModel"]] = relationship(
        back_populates="lending",
    )

    cost_center: Mapped[CostCenterTOTVSModel] = relationship()
    cost_center_id = Column(
        "cost_center_id", ForeignKey(CostCenterTOTVSModel.id), nullable=False
    )

    # código gerado
    number = Column("number", String(length=30), nullable=True)
    manager = Column("manager", String(length=50))
    business_executive = Column("business_executive", String(length=50), nullable=True)
    project = Column("project", String(length=100), nullable=True)
    location = Column("location", String(length=100), nullable=True)
    observations = Column("observations", String(length=255), nullable=True)
    signed_date = Column("signed_date", Date, nullable=True)
    revoke_signed_date = Column("revoke_signed_date", Date, nullable=True)
    glpi_number = Column("glpi_number", String(length=25), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id} - {self.number} ({self.type.name})"


class WitnessModel(Base):
    """Witness model"""

    __tablename__ = "witness"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    employee: Mapped[EmployeeModel] = relationship()
    employee_id = Column("employee_id", ForeignKey(EmployeeModel.id), nullable=False)
    lending: Mapped[LendingModel] = relationship(back_populates="witnesses")
    lending_id = Column("lending_id", ForeignKey(LendingModel.id), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id}"
