"""Maintenance models"""

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from src.asset.models import AssetModel
from src.database import Base
from src.people.models import EmployeeModel


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
    action_id = Column(
        "action_id", ForeignKey(MaintenanceActionModel.id), nullable=False
    )

    status: Mapped[MaintenanceStatusModel] = relationship()
    status_id = Column(
        "status_id", ForeignKey(MaintenanceStatusModel.id), nullable=False
    )

    asset: Mapped[AssetModel] = relationship()
    asset_id = Column("asset_id", ForeignKey(AssetModel.id), nullable=False)

    employee: Mapped[EmployeeModel] = relationship()
    employee_id = Column("employee_id", ForeignKey(EmployeeModel.id), nullable=False)

    attachments = relationship(
        "MaintenanceAttachmentModel", back_populates="maintenance"
    )

    open_date = Column("open_date", Date)
    close_date = Column("close_date", Date, nullable=True)
    glpi_number = Column("gpli_number", String(length=50), nullable=True)
    open_date_glpi = Column("open_date_glpi", Date, nullable=True)
    open_date_supplier = Column("open_date_supplier", Date, nullable=True)
    # chamado do fonecedor
    supplier_number = Column("supplier_number", String(length=50), nullable=True)
    supplier_service_order = Column(
        "supplier_service_order", String(length=50), nullable=True
    )
    incident_description = Column(
        "incident_description", String(length=255), nullable=True
    )
    resolution = Column("resolution", String(length=255), nullable=True)
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


class UpgradeAttachmentModel(Base):
    """Upgrade attachment model"""

    __tablename__ = "upgrade_attachment"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    upgrade: Mapped["UpgradeModel"] = relationship(back_populates="attachments")
    upgrade_id = Column("upgrade_id", ForeignKey("upgrade.id"))

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
    status_id = Column("status_id", ForeignKey(MaintenanceStatusModel.id))

    asset: Mapped[AssetModel] = relationship()
    asset_id = Column("asset_id", ForeignKey(AssetModel.id), nullable=False)

    employee: Mapped[EmployeeModel] = relationship()
    employee_id = Column("employee_id", ForeignKey(EmployeeModel.id), nullable=False)

    attachments = relationship("UpgradeAttachmentModel", back_populates="upgrade")

    open_date = Column("open_date", Date)
    close_date = Column("close_date", Date, nullable=True)
    value = Column("value", Float, nullable=True)
    detailing = Column("detailing", String(length=255), nullable=True)
    supplier = Column("supplier", String(length=100), nullable=True)
    invoice_number = Column("invoice_number", String(length=100), nullable=True)
    observations = Column("observations", String(length=255), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id}"
