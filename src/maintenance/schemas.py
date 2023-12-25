"""Maintenance schemas"""
from datetime import date
from typing import List, Optional

from pydantic import Field

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

    action_id: int
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    supplier_service_order: Optional[str] = Field(
        alias="supplierServiceOrder", default=None
    )
    supplier_number: Optional[str] = Field(alias="supplierNumber", default=None)


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
    open_date: date = Field(alias="openDate")
    close_date: Optional[date] = Field(alias="closeDate", default=None)
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    supplier_service_order: Optional[str] = Field(
        alias="supplierServiceOrder", default=None
    )
    supplier_number: Optional[str] = Field(alias="supplierNumber", default=None)
    resolution: Optional[str] = None
    attachments: List[MaintenanceAttachmentSerializerSchema] = []


class UpgradeSerializerSchema(BaseSchema):
    """Upgrade serializer schema"""

    id: int
    status: str
    open_date: date = Field(alias="openDate")
    close_date: Optional[date] = Field(alias="closeDate", default=None)
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    detailing: Optional[str]
    supplier: Optional[str]
    observations: Optional[str]
