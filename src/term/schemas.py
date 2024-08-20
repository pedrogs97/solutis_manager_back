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
    XGG = "XGG"


class TermItemSerializerSchema(BaseSchema):
    """Term Item serializer schema"""

    id: int
    description: Optional[str]
    size: Optional[SizesEnum]
    quantity: Optional[int]
    value: Optional[float]
    line_number: Optional[str] = Field(serialization_alias="lineNumber")
    operator: Optional[str]


class TermItemTypeSerializerSchema(BaseSchema):
    """Term Item serializer schema"""

    id: int
    name: str


class TermSerializerSchema(BaseSchema):
    """Term serializer schema"""

    id: int
    employee: EmployeeSerializerSchema
    number: Optional[str] = None
    document: Optional[int]
    document_revoke: Optional[int] = Field(serialization_alias="documentRevoke")
    workload: Optional[WorkloadSerializerSchema] = None
    cost_center: CostCenterSerializerSchema = Field(serialization_alias="costCenter")
    type: TermItemTypeSerializerSchema
    status: str
    manager: str
    observations: Optional[str]
    signed_date: Optional[str] = Field(serialization_alias="signedDate")
    revoke_signed_date: Optional[str] = Field(serialization_alias="revokeSignedDate")
    project: Optional[str] = None
    business_executive: Optional[str] = Field(
        serialization_alias="businessExecutive", default=None
    )
    location: str
    item: TermItemSerializerSchema
    created_at: str = Field(serialization_alias="createdAt")


class UpdateTermSchema(BaseSchema):
    """Update term"""

    observations: Optional[str]


class NewTermSchema(BaseSchema):
    """New term schema"""

    employee_id: int = Field(alias="employeeId")
    workload_id: Optional[int] = Field(alias="workloadId", default=None)
    cost_center_id: int = Field(alias="costCenterId")
    type: int = Field(alias="type")
    manager: str
    observations: Optional[str] = None
    project: Optional[str] = None
    business_executive: str = Field(alias="businessExecutive", default=None)
    location: str
    description: Optional[str] = None
    size: Optional[SizesEnum] = None
    quantity: Optional[int] = None
    value: Optional[float] = None
    line_number: Optional[str] = Field(alias="lineNumber", default=None)
    operator: Optional[str] = None


class TermEmployeeHistorySerializerSchema(BaseSchema):
    """Term history serializer schema"""

    id: int
    employee: EmployeeShortSerializerSchema
    document: Optional[int]
    document_revoke: Optional[int] = Field(serialization_alias="documentRevoke")
    cost_center: CostCenterSerializerSchema = Field(serialization_alias="costCenter")
    workload: str
    status: Optional[str]
    type: str
    term_item: TermItemSerializerSchema = Field(serialization_alias="termItem")
    number: Optional[str]
    observations: Optional[str]
    signed_date: Optional[str] = Field(serialization_alias="signedDate")
    revoke_signed_date: Optional[str] = Field(serialization_alias="revokeSignedDate")
    project: str
