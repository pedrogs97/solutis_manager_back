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
    supplier_service_order: Optional[str] = Field(
        alias="supplierServiceOrder", default=None
    )
    supplier_number: Optional[str] = Field(alias="supplierNumber", default=None)
    asset_id: int = Field(alias="assetId")
    employee_id: int = Field(alias="employeeId")


class UpdateMaintenanceSchema(BaseSchema):
    """Update Maintenance schema"""

    status_id: int
    close_date: Optional[date] = Field(alias="closeDate", default=None)
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    supplier_service_order: Optional[str] = Field(
        alias="supplierServiceOrder", default=None
    )
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
    supplier_service_order: Optional[str] = Field(
        serialization_alias="supplierServiceOrder", default=None
    )
    supplier_number: Optional[str] = Field(
        serialization_alias="supplierNumber", default=None
    )
    resolution: Optional[str] = None
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
    observations: Optional[str] = None


class UpdateUpgradeSchema(BaseSchema):
    """Update Upgrade schema"""

    detailing: Optional[str] = None
    observations: Optional[str] = None
    status_id: int
    close_date: Optional[date] = Field(alias="closeDate", default=None)


class UpgradeSerializerSchema(BaseSchema):
    """Upgrade serializer schema"""

    id: int
    status: str
    open_date: date = Field(serialization_alias="openDate")
    close_date: Optional[date] = Field(serialization_alias="closeDate", default=None)
    glpi_number: Optional[str] = Field(serialization_alias="glpiNumber", default=None)
    detailing: Optional[str]
    supplier: Optional[str]
    asset: AssetShortSerializerSchema
    employee: EmployeeShortSerializerSchema
    observations: Optional[str]
