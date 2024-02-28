"""Term schemas"""

from enum import Enum
from typing import Optional

from pydantic import Field

from src.lending.schemas import CostCenterSerializerSchema, WorkloadSerializerSchema
from src.people.schemas import EmployeeSerializerSchema, EmployeeShortSerializerSchema
from src.schemas import BaseSchema


class SizesEnum(str, Enum):
    """Sizes enum"""

    PP = "PP"
    P = "P"
    M = "M"
    G = "G"
    GG = "GG"
    XG = "XG"


class TermItemSerializerSchema(BaseSchema):
    """Term Item serializer schema"""

    id: int
    description: Optional[str]
    size: Optional[str]
    quantity: Optional[int]
    value: Optional[float]


class TermSerializerSchema(BaseSchema):
    """Term serializer schema"""

    id: int
    employee: EmployeeSerializerSchema
    number: Optional[str] = None
    document: Optional[int]
    document_revoke: Optional[int] = Field(serialization_alias="documentRevoke")
    workload: Optional[WorkloadSerializerSchema] = None
    cost_center: CostCenterSerializerSchema = Field(serialization_alias="costCenter")
    type: str
    status: str
    manager: str
    observations: Optional[str]
    signed_date: Optional[str] = Field(serialization_alias="signedDate")
    revoke_signed_date: Optional[str] = Field(serialization_alias="revokeSignedDate")
    glpi_number: Optional[str] = Field(serialization_alias="glpiNumber")
    project: Optional[str] = None
    business_executive: Optional[str] = Field(
        serialization_alias="businessExecutive", default=None
    )
    location: str
    item: TermItemSerializerSchema


class TermAssetHistorySerializerSchema(BaseSchema):
    """Term history serializer schema"""

    id: int
    employee: EmployeeShortSerializerSchema
    number: Optional[str]
    document: Optional[int]
    document_revoke: Optional[int] = Field(serialization_alias="documentRevoke")
    workload: str
    cost_center: CostCenterSerializerSchema = Field(serialization_alias="costCenter")
    type: str
    status: Optional[str]
    observations: Optional[str]
    signed_date: Optional[str] = Field(serialization_alias="signedDate")
    revoke_signed_date: Optional[str] = Field(serialization_alias="revokeSignedDate")
    glpi_number: Optional[str] = Field(serialization_alias="glpiNumber")
    project: str


class UpdateTermSchema(BaseSchema):
    """Update term"""

    observations: Optional[str]


class NewTermSchema(BaseSchema):
    """New term schema"""

    employee_id: int = Field(alias="employeeId")
    workload_id: Optional[int] = Field(alias="workloadId", default=None)
    cost_center_id: int = Field(alias="costCenterId")
    type_id: int = Field(alias="typeId")
    manager: str
    observations: Optional[str] = None
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    project: Optional[str] = None
    business_executive: str = Field(alias="businessExecutive", default=None)
    location: str
    description: Optional[str] = None
    size: Optional[SizesEnum] = None
    quantity: Optional[int] = None
    value: Optional[float] = None
