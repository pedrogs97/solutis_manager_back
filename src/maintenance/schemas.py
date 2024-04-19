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


class MaintenanceCriticalityModelSerializerSchema(BaseSchema):
    """Maintenance status schema"""

    id: int
    name: str


class NewMaintenanceSchema(BaseSchema):
    """New Maintenance schema"""

    action_id: int = Field(alias="actionId")
    criticality_id: Optional[int] = Field(alias="criticalityId", default=None)
    asset_id: int = Field(alias="assetId")
    employee_id: int = Field(alias="employeeId")
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    open_date_glpi: Optional[date] = Field(alias="openDateGlpi", default=None)
    open_date_supplier: Optional[date] = Field(alias="openDateSupplier", default=None)
    supplier_number: Optional[str] = Field(alias="supplierNumber", default=None)
    incident_description: Optional[str] = Field(
        alias="incidentDescription", default=None
    )
    resolution: Optional[str] = None
    value: Optional[float] = None
    has_assurance: Optional[bool] = Field(alias="hasAssurance", default=False)


class UpdateMaintenanceSchema(BaseSchema):
    """Update Maintenance schema"""

    criticality_id: Optional[int] = Field(alias="criticalityId", default=None)
    close: Optional[bool] = False
    open_date_supplier: Optional[date] = Field(alias="openDateSupplier", default=None)
    supplier_number: Optional[str] = Field(alias="supplierNumber", default=None)
    resolution: Optional[str] = None
    in_progress: Optional[bool] = Field(alias="inProgress", default=False)
    value: Optional[float] = None
    has_assurance: Optional[bool] = Field(alias="hasAssurance", default=False)


class MaintenanceAttachmentSerializerSchema(BaseSchema):
    """Maintenance attachment serializer schema"""

    id: int
    path: Optional[str]
    file_name: Optional[str] = Field(serialization_alias="fileName", default=None)


class MaintenanceSerializerSchema(BaseSchema):
    """Maintenance serializer schema"""

    id: int
    action: MaintenanceActionSerializerSchema
    status: str
    criticality: Optional[MaintenanceCriticalityModelSerializerSchema] = None
    value: float
    has_assurance: Optional[bool] = Field(
        serialization_alias="hasAssurance", default=False
    )
    open_date: str = Field(serialization_alias="openDate")
    close_date: Optional[str] = Field(serialization_alias="closeDate", default=None)
    glpi_number: Optional[str] = Field(serialization_alias="glpiNumber", default=None)
    open_date_glpi: Optional[str] = Field(
        serialization_alias="openDateGlpi", default=None
    )
    supplier_service_order: Optional[str] = Field(
        serialization_alias="supplierServiceOrder", default=None
    )
    open_date_supplier: Optional[str] = Field(
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
    value: Optional[float] = None
    detailing: Optional[str] = None
    supplier: Optional[str] = None
    invoice_number: Optional[str] = Field(alias="invoiceNumber", default=None)
    observations: Optional[str] = None


class UpdateUpgradeSchema(BaseSchema):
    """Update Upgrade schema"""

    detailing: Optional[str] = None
    observations: Optional[str] = None
    invoice_number: Optional[str] = Field(alias="invoiceNumber", default=None)
    close: Optional[bool] = False
    in_progress: Optional[bool] = Field(alias="inProgress", default=False)
    value: Optional[float] = None


class UpgradeAttachmentSerializerSchema(BaseSchema):
    """Upgrade attachment serializer schema"""

    id: int
    path: Optional[str]
    file_name: Optional[str] = Field(serialization_alias="fileName", default=None)


class UpgradeSerializerSchema(BaseSchema):
    """Upgrade serializer schema"""

    id: int
    status: str
    open_date: str = Field(serialization_alias="openDate")
    close_date: Optional[str] = Field(serialization_alias="closeDate", default=None)
    value: Optional[float]
    detailing: Optional[str]
    supplier: Optional[str]
    invoice_number: Optional[str] = Field(
        serialization_alias="invoiceNumber", default=None
    )
    asset: AssetShortSerializerSchema
    employee: EmployeeShortSerializerSchema
    observations: Optional[str]
    attachments: List[UpgradeAttachmentSerializerSchema] = []
