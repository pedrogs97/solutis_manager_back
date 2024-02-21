"""Maintenance schemas"""

from datetime import date
from typing import List, Optional

from pydantic import Field

from src.asset.schemas import AssetShortSerializerSchema
from src.people.schemas import EmployeeShortSerializerSchema
from src.schemas import BaseSchema


class MaintenanceActionSerializerSchema(BaseSchema):
    """Maintenance action serializer schema"""

    id: int
    name: str


class MaintenanceStatusSerializerSchema(BaseSchema):
    """Maintenance status schema"""

    id: int
    name: str


class NewMaintenanceSchema(BaseSchema):
    """New Maintenance schema"""

    action_id: int = Field(alias="actionId")
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    open_date_glpi: Optional[date] = Field(alias="openDateGlpi", default=None)
    open_date_supplier: Optional[date] = Field(alias="openDateSupplier", default=None)
    supplier_number: Optional[str] = Field(alias="supplierNumber", default=None)
    incident_description: Optional[str] = Field(
        alias="incidentDescription", default=None
    )
    asset_id: int = Field(alias="assetId")
    employee_id: int = Field(alias="employeeId")


class UpdateMaintenanceSchema(BaseSchema):
    """Update Maintenance schema"""

    status_id: int
    close: Optional[bool] = False
    open_date_supplier: Optional[date] = Field(alias="openDateSupplier", default=None)
    supplier_number: Optional[str] = Field(alias="supplierNumber", default=None)
    resolution: Optional[str] = None


class MaintenanceAttachmentSerializerSchema(BaseSchema):
    """Maintenance attachment serializer schema"""

    id: int
    path: Optional[str]
    file_name: str = Field(alias="fileName")


class MaintenanceSerializerSchema(BaseSchema):
    """Maintenance serializer schema"""

    id: int
    action: str
    status: str
    open_date: str = Field(serialization_alias="openDate")
    close_date: Optional[str] = Field(serialization_alias="closeDate", default=None)
    glpi_number: Optional[str] = Field(serialization_alias="glpiNumber", default=None)
    open_date_glpi: Optional[date] = Field(
        serialization_alias="openDateGlpi", default=None
    )
    supplier_service_order: Optional[str] = Field(
        serialization_alias="supplierServiceOrder", default=None
    )
    open_date_supplier: Optional[date] = Field(
        serialization_alias="openDateSupplier", default=None
    )
    supplier_number: Optional[str] = Field(
        serialization_alias="supplierNumber", default=None
    )
    resolution: Optional[str] = None
    incident_description: Optional[str] = Field(
        serialization_alias="incidentDescription", default=None
    )
    asset: AssetShortSerializerSchema
    employee: EmployeeShortSerializerSchema
    attachments: List[MaintenanceAttachmentSerializerSchema] = []


class NewUpgradeSchema(BaseSchema):
    """New Upgrade schema"""

    asset_id: int = Field(alias="assetId")
    employee_id: int = Field(alias="employeeId")
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    detailing: Optional[str] = None
    supplier: Optional[str] = None
    invoice_number: Optional[str] = Field(alias="invoiceNumber", default=None)
    observations: Optional[str] = None


class UpdateUpgradeSchema(BaseSchema):
    """Update Upgrade schema"""

    status_id: int
    detailing: Optional[str] = None
    observations: Optional[str] = None
    invoice_number: Optional[str] = Field(alias="invoiceNumber", default=None)
    close: Optional[bool] = False


class UpgradeAttachmentSerializerSchema(BaseSchema):
    """Upgrade attachment serializer schema"""

    id: int
    path: Optional[str]
    file_name: str = Field(alias="fileName")


class UpgradeSerializerSchema(BaseSchema):
    """Upgrade serializer schema"""

    id: int
    status: str
    open_date: str = Field(serialization_alias="openDate")
    close_date: Optional[str] = Field(serialization_alias="closeDate", default=None)
    glpi_number: Optional[str] = Field(serialization_alias="glpiNumber", default=None)
    detailing: Optional[str]
    supplier: Optional[str]
    invoice_number: Optional[str] = Field(
        serialization_alias="invoiceNumber", default=None
    )
    asset: AssetShortSerializerSchema
    employee: EmployeeShortSerializerSchema
    observations: Optional[str]
    attachments: List[UpgradeAttachmentSerializerSchema] = []
