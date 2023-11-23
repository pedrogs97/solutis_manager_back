"""Lending models"""
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, relationship

from src.database import Base
from src.invoice.models import InvoiceModel, invoice_assets
from src.people.models import EmployeeModel


class AssetTypeModel(Base):
    """
    Asset type model

    * Computadores e Periféricos
    * Máquinas e equipamentos
    * Móveis e utensilios
    * Veículos
    * Instalações
    * Benfeitorias em Imóveis
    * Softwares Admnistrativos
    """

    __tablename__ = "asset_type"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=25), nullable=False)
    group_code = Column("group_code", String(length=150), nullable=False)
    name = Column("name", String(length=150), nullable=False)
    acronym = Column("acronym", String(length=3), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.acronym} - {self.name}"


class AssetStatusModel(Base):
    """
    Asset status model

    * Disponível
    * Comodato
    * Estoque SP
    * Estoque BA
    * Reservado
    * Inativo
    * Empréstimo
    * Descarte
    """

    __tablename__ = "asset_status"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=20), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class AssetClothingSizeModel(Base):
    """
    Asset clothing size model

    * PP
    * P
    * M
    * G
    * GG
    * XG
    """

    __tablename__ = "asset_clothing_size"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=5), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class AssetModel(Base):
    """Asset model"""

    __tablename__ = "asset"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    type: Mapped[AssetTypeModel] = relationship()
    type_id = Column("type_id", ForeignKey("asset_type.id"), nullable=False)

    status_id = Column("status_id", ForeignKey("asset_status.id"), nullable=False)
    status: Mapped[AssetStatusModel] = relationship()

    clothing_size_id = Column(
        "clothing_size_id", ForeignKey("asset_clothing_size.id"), nullable=False
    )
    clothing_size: Mapped[AssetClothingSizeModel] = relationship()

    invoices: Mapped[List[InvoiceModel]] = relationship(
        secondary=invoice_assets, back_populates="assets"
    )

    code = Column("code", String(length=255), nullable=True)
    # tombo - registro patrimonial
    register_number = Column("register_number", String(length=255), nullable=True)
    description = Column("description", String(length=255), nullable=True)
    # fornecedor
    supplier = Column("supplier", String(length=100), nullable=True)
    assurance_date = Column("assurance_date", String(length=150), nullable=True)
    observations = Column("observations", String(length=255), nullable=True)
    discard_reason = Column("discard_reason", String(length=255), nullable=True)
    # padrão
    pattern = Column("pattern", String(length=100), nullable=True)
    operational_system = Column("operational_system", String(length=100), nullable=True)
    serial_number = Column("serial_number", String(length=255), nullable=True)
    imei = Column("imei", String(length=255), nullable=True)
    acquisition_date = Column("acquisition_date", DateTime, nullable=True)
    value = Column("value", Float, nullable=True)
    # pacote office
    ms_office = Column("ms_office", Boolean, nullable=True)
    line_number = Column("line_number", String(length=20), nullable=True)
    # operadora
    operator = Column("operator", String(length=50), nullable=True)
    # modelo
    model = Column("model", String(length=100), nullable=True)
    # acessórios
    accessories = Column("accessories", String(length=255), nullable=True)
    configuration = Column("configuration", String(length=255), nullable=True)
    quantity = Column("quantity", Integer, nullable=True, default=1)
    unit = Column("unit", String(length=10), nullable=True)
    active = Column("active", Boolean, nullable=True, default=True)
    by_agile = Column("by_agile", Boolean, nullable=True, default=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.code} - {self.description}"


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


lending_witnesses = Table(
    "lending_witnesses",
    Base.metadata,
    Column("lending_id", ForeignKey("lending.id")),
    Column("witness_id", ForeignKey("witness.id")),
)


class CostCenterModel(Base):
    """Cost center model"""

    __tablename__ = "cost_center"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=25), nullable=False)
    name = Column("name", String(length=60), nullable=False)
    classification = Column("group_name", String(length=60), nullable=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.code}"


class WitnessModel(Base):
    """Witness model"""

    __tablename__ = "witness"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    employee: Mapped[EmployeeModel] = relationship()
    employee_id = Column("employee_id", ForeignKey("employees.id"), nullable=False)
    lendings = relationship(
        "LendingModel", secondary=lending_witnesses, back_populates="witnesses"
    )

    signed = Column("signed", Date, nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id}"


class LendingModel(Base):
    """Lending model"""

    __tablename__ = "lending"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    employee: Mapped[EmployeeModel] = relationship()
    employee_id = Column("employee_id", ForeignKey("employees.id"), nullable=False)

    asset: Mapped[AssetModel] = relationship()
    asset_id = Column("asset_id", ForeignKey("asset.id"), nullable=False)

    document: Mapped[DocumentModel] = relationship()
    document_id = Column("document_id", ForeignKey("document.id"), nullable=True)
    # lotação
    workload: Mapped[WorkloadModel] = relationship()
    workload_id = Column("workload_id", ForeignKey("workload.id"), nullable=False)

    witnesses: Mapped[List[WitnessModel]] = relationship(
        secondary=lending_witnesses,
        back_populates="lendings",
    )

    cost_center: Mapped[CostCenterModel] = relationship()
    cost_center_id = Column(
        "cost_center_id", ForeignKey("cost_center.id"), nullable=False
    )

    # código gerado
    number = Column("number", String(length=30), nullable=True)
    manager = Column("manager", String(length=50))
    observations = Column("observations", String(length=255), nullable=True)
    signed_date = Column("signed_date", Date, nullable=True)
    glpi_number = Column("glpi_number", String(length=25), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id} - {self.number}"


class MaintenanceActionModel(Base):
    """
    Maintenance action model

    * Manutenção externa
    * Manutenção interna
    """

    __tablename__ = "maintenance_action"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=20), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class MaintenanceStatusModel(Base):
    """
    Maintenance action model

    * Em progresso
    * Pendente
    * Finalizado
    """

    __tablename__ = "maintenance_status"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=15), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class MaintenanceModel(Base):
    """Maintenance model"""

    __tablename__ = "maintenance"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    action: Mapped[MaintenanceActionModel] = relationship()
    action_id = Column("action_id", ForeignKey("maintenance_action.id"), nullable=False)

    status: Mapped[MaintenanceStatusModel] = relationship()
    status_id = Column("status_id", ForeignKey("maintenance_status.id"), nullable=False)

    attachments = relationship(
        "MaintenanceAttachmentModel", back_populates="maintenance"
    )

    open_date = Column("open_date", Date)
    close_date = Column("close_date", Date, nullable=True)
    glpi_number = Column("gpli_number", String(length=50), nullable=True)
    supplier_service_order = Column(
        "supplier_service_order", String(length=50), nullable=True
    )
    supplier_number = Column("supplier_number", String(length=50), nullable=True)
    resolution = Column("resolution", String(length=255), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id}"


class MaintenanceAttachmentModel(Base):
    """Maintenance attachment model"""

    __tablename__ = "maintenance_attachment"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    maintenance: Mapped[MaintenanceModel] = relationship(back_populates="attachments")
    maintenance_id = Column("maintenance_id", ForeignKey("maintenance.id"))

    path = Column(String(length=255), nullable=True)
    file_name = Column(String(length=100))

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.file_name}"


class UpgradeModel(Base):
    """Upgrade model"""

    __tablename__ = "upgrade"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    status: Mapped[MaintenanceStatusModel] = relationship()
    status_id = Column("status_id", ForeignKey("maintenance_status.id"))

    open_date = Column("open_date", Date)
    close_date = Column("close_date", Date, nullable=True)
    glpi_number = Column("glpi_number", String(length=50), nullable=True)
    detailing = Column("detailing", String(length=255), nullable=True)
    supplier = Column("supplier", String(length=100), nullable=True)
    observations = Column("observations", String(length=255), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id}"


class VerificationModel(Base):
    """Verification model"""

    __tablename__ = "verification"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    asset_type: Mapped[AssetTypeModel] = relationship()
    asset_type_id = Column("asset_type_id", ForeignKey("asset_type.id"), nullable=False)

    question = Column("question", String(length=100))
    step = Column("step", String(length=2))

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.question}"


class VerificationTypeModel(Base):
    """Verification type model

    * Envio
    * Retorno
    """

    __tablename__ = "verification_type"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=100))

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class VerificationAnswerModel(Base):
    """Verification answer model"""

    __tablename__ = "verification_answer"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    lending: Mapped[LendingModel] = relationship()
    lending_id = Column("lending_id", ForeignKey("lending.id"), nullable=False)

    verification: Mapped[VerificationModel] = relationship()
    verification_id = Column("verification_id", ForeignKey("verification.id"))

    type: Mapped[VerificationTypeModel] = relationship()
    type_id = Column("type_id", ForeignKey("verification_type.id"))

    answer = Column("answer", String(length=100), nullable=False)
    observations = Column("observations", String(length=255), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id}"
