"""Asset models"""

from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, relationship

from src.config import DEFAULT_DATE_FORMAT
from src.database import Base
from src.datasync.models import AssetTypeTOTVSModel
from src.invoice.models import InvoiceModel


class AssetTypeModel(Base):
    """
    Asset type model

    * NOTEBOOK
    * DESKTOP
    * MONITOR
    * WEBCAM
    * TELEFONIA
    * VESTIMENTA
    * FERRAMENTAS
    * IMPRESSORA
    * TABLET
    * HEADSET
    * MOUSE/TECLADO
    * HD EXTERNO
    * PENDRIVE
    """

    __tablename__ = "asset_type"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=25), nullable=False, unique=True)
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


class AssetStatusHistoricModel(Base):
    """Asset status history model"""

    __tablename__ = "asset_status_history"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    asset: Mapped["AssetModel"] = relationship()
    asset_id = Column("asset_id", ForeignKey("asset.id"), nullable=False)

    status: Mapped[AssetStatusModel] = relationship()
    status_id = Column("status_id", ForeignKey(AssetStatusModel.id), nullable=False)

    created_at = Column(
        "created_at", DateTime, nullable=False, server_default=func.now()
    )

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.asset}: {self.status} - {self.created_at.strftime(DEFAULT_DATE_FORMAT)}"


class AssetModel(Base):
    """Asset model"""

    __tablename__ = "asset"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    asset_group: Mapped[AssetTypeTOTVSModel] = relationship()
    asset_group_id = Column(
        "asset_group_id", ForeignKey(AssetTypeTOTVSModel.id), nullable=True
    )

    type: Mapped[AssetTypeModel] = relationship(lazy="joined")
    type_id = Column("type_id", ForeignKey(AssetTypeModel.id), nullable=True)

    status_id = Column(
        "status_id", ForeignKey(AssetStatusModel.id), nullable=True, default=1
    )
    status: Mapped[AssetStatusModel] = relationship(lazy="joined")

    invoice: Mapped[InvoiceModel] = relationship(back_populates="assets")
    invoice_id = Column("invoice_id", ForeignKey(InvoiceModel.id), nullable=True)

    maintenances: Mapped[List["MaintenanceModel"]] = relationship(viewonly=True)
    upgrades: Mapped[List["UpgradeModel"]] = relationship(viewonly=True)
    disposals: Mapped[List["AssetDisposalModel"]] = relationship(viewonly=True)

    code = Column("code", String(length=255), nullable=True, unique=True)
    # tombo - registro patrimonial
    register_number = Column("register_number", String(length=255), nullable=True)
    description = Column("description", String(length=255), nullable=True)
    # fornecedor
    supplier = Column("supplier", String(length=100), nullable=True)
    assurance_date = Column("assurance_date", String(length=150), nullable=True)
    observations = Column("observations", String(length=999), nullable=True)
    # padrão
    pattern = Column("pattern", String(length=100), nullable=True)
    brand = Column("brand", String(length=150), nullable=True)
    operational_system = Column("operational_system", String(length=100), nullable=True)
    serial_number = Column("serial_number", String(length=255), nullable=True)
    imei = Column("imei", String(length=255), nullable=True)
    acquisition_date = Column("acquisition_date", DateTime, nullable=True)
    value = Column("value", Float, nullable=True)
    depreciation = Column("depreciation", Float, nullable=True)
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

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.code} - {self.description}"


class AssetDisposalModel(Base):
    """Asset disposal model"""

    __tablename__ = "asset_disposal"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    asset: Mapped[AssetModel] = relationship(lazy="joined")
    asset_id = Column("asset_id", ForeignKey(AssetModel.id))

    asset_disposal_attachments: Mapped[
        List["AssetDisposalAttachmentModel"]
    ] = relationship(viewonly=True)

    disposal_date = Column("write_off_date", DateTime, nullable=False)
    reason = Column("reason", String(length=15), nullable=False)
    justification = Column("justification", String(length=255), nullable=True)
    observations = Column("observations", String(length=255), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.asset} - {self.reason} ({self.disposal_date.strftime(DEFAULT_DATE_FORMAT)})"


class AssetDisposalAttachmentModel(Base):
    """Asset disposal attachment model"""

    __tablename__ = "asset_disposal_attachment"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    disposal: Mapped[AssetDisposalModel] = relationship(
        back_populates="asset_disposal_attachments"
    )
    disposal_id = Column("disposal_id", ForeignKey(AssetDisposalModel.id))

    path = Column("path", String(length=255), nullable=True)
    file_name = Column("file_name", String(length=255), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.file_name} - {self.path}"
