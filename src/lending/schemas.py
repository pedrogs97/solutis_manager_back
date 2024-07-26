"""Lending schemas"""

from enum import Enum
from typing import List, Optional

from pydantic import Field

from src.asset.schemas import AssetShortSerializerSchema
from src.people.schemas import EmployeeSerializerSchema, EmployeeShortSerializerSchema
from src.schemas import BaseSchema


class LendingBUEnum(str, Enum):
    """BU choices"""

    ADS = "ADS"
    CSA = "CSA"
    BPS = "BPS"
    CORP = "CORP"


class CostCenterTotvsSchema(BaseSchema):
    """Cost center schema"""

    code: str
    name: str
    classification: str


class CostCenterSerializerSchema(BaseSchema):
    """Cost center serializer schema"""

    id: int
    code: str
    name: str
    classification: str


class WorkloadSerializerSchema(BaseSchema):
    """Workload serializer schema"""

    id: int
    name: str


class WitnessSerializerSchema(BaseSchema):
    """Witness serializer schema"""

    id: int
    employee: EmployeeSerializerSchema


class LendingSerializerSchema(BaseSchema):
    """Lending serializer schema"""

    id: int
    employee: EmployeeSerializerSchema
    asset: AssetShortSerializerSchema
    number: Optional[str] = None
    document: Optional[int]
    document_revoke: Optional[int] = Field(serialization_alias="documentRevoke")
    workload: Optional[WorkloadSerializerSchema] = None
    witnesses: Optional[List[WitnessSerializerSchema]] = []
    cost_center: CostCenterSerializerSchema = Field(serialization_alias="costCenter")
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
    ms_office: bool = Field(serialization_alias="msOffice", default=False)
    location: str
    bu: Optional[LendingBUEnum] = None
    deleted: bool = False
    created_at: str = Field(serialization_alias="createdAt")


class LendingAssetHistorySerializerSchema(BaseSchema):
    """Lending history serializer schema"""

    id: int
    employee: EmployeeShortSerializerSchema
    asset: int
    number: Optional[str]
    document: Optional[int]
    document_revoke: Optional[int] = Field(serialization_alias="documentRevoke")
    workload: str
    witnesses: List[int]
    cost_center: CostCenterSerializerSchema = Field(serialization_alias="costCenter")
    status: Optional[str]
    observations: Optional[str]
    signed_date: Optional[str] = Field(serialization_alias="signedDate")
    revoke_signed_date: Optional[str] = Field(serialization_alias="revokeSignedDate")
    glpi_number: Optional[str] = Field(serialization_alias="glpiNumber")
    project: str
    ms_office: bool = Field(serialization_alias="msOffice", default=False)


class UpdateLendingSchema(BaseSchema):
    """Update lending"""

    observations: Optional[str]
    ms_office: Optional[bool] = Field(alias="msOffice", default=None)
    manager: Optional[str] = None
    project: Optional[str] = None
    business_executive: Optional[str] = Field(alias="businessExecutive", default=None)
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)


class NewLendingSchema(BaseSchema):
    """New lending schema"""

    employee_id: int = Field(alias="employeeId")
    asset_id: int = Field(alias="assetId")
    workload_id: Optional[int] = Field(alias="workloadId", default=None)
    witnesses_id: Optional[List[int]] = Field(alias="witnessesId", default=[])
    cost_center_id: int = Field(alias="costCenterId")
    manager: str
    observations: Optional[str] = None
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    project: Optional[str] = None
    business_executive: str = Field(alias="businessExecutive", default=None)
    location: str
    bu: LendingBUEnum
    ms_office: bool = Field(alias="msOffice", default=False)


class CreateWitnessSchema(BaseSchema):
    """Create witness schema"""

    employee_id: int = Field(alias="employeeId")
