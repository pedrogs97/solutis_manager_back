"""Lending schemas"""

from datetime import date
from typing import List, Optional

from pydantic import Field

from src.asset.schemas import AssetShortSerializerSchema
from src.people.schemas import EmployeeSerializerSchema
from src.schemas import BaseSchema


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


class DocumentTypeSerializerSchema(BaseSchema):
    """Document type serializer schema"""

    id: int
    name: str


class DocumentSerializerSchema(BaseSchema):
    """Document serializer schema"""

    id: int
    type: str
    path: Optional[str]
    file_name: str = Field(serialization_alias="fileName")


class WorkloadSerializerSchema(BaseSchema):
    """Workload serializer schema"""

    id: int
    name: str


class WitnessSerializerSchema(BaseSchema):
    """Witness serializer schema"""

    id: int
    employee: EmployeeSerializerSchema
    signed: Optional[str]


class LendingSerializerSchema(BaseSchema):
    """Lending serializer schema"""

    id: int
    employee: EmployeeSerializerSchema
    asset: AssetShortSerializerSchema
    document: Optional[int]
    workload: WorkloadSerializerSchema
    witnesses: List[WitnessSerializerSchema]
    cost_center: CostCenterSerializerSchema = Field(serialization_alias="costCenter")
    type: str
    status: str
    manager: str
    observations: Optional[str]
    signed_date: Optional[str] = Field(serialization_alias="signedDate")
    glpi_number: Optional[str] = Field(serialization_alias="glpiNumber")
    goal: Optional[str] = Field(alias="goal", default=None)
    project: Optional[str] = None
    business_executive: str = Field(alias="businessExecutive", default=None)
    location: str


class NewLendingSchema(BaseSchema):
    """New lending schema"""

    employee_id: int = Field(alias="employeeId")
    asset_id: int = Field(alias="assetId")
    workload_id: int = Field(alias="workloadId")
    witnesses_id: List[int] = Field(alias="witnessesId")
    cost_center_id: int = Field(alias="costCenterId")
    type_id: int = Field(alias="typeId")
    manager: str
    observations: Optional[str] = None
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    goal: Optional[str] = Field(alias="goal", default=None)
    project: Optional[str] = None
    business_executive: str = Field(alias="businessExecutive", default=None)
    location: str


class NewLendingDocSchema(BaseSchema):
    """New contract info schema"""

    employee_id: int = Field(alias="employeeId")
    lending_id: int = Field(alias="lendingId")
    legal_person: bool = Field(alias="legalPerson", default=False)


class NewRevokeContractDocSchema(BaseSchema):
    """New contract info schema"""

    lending_id: int = Field(alias="lendingId")
    legal_person: bool = Field(alias="legalPerson", default=False)


class WitnessContextSchema(BaseSchema):
    """Witness context for template"""

    full_name: str
    taxpayer_identification: str


class NewLendingContextSchema(BaseSchema):
    """Context for contract template"""

    number: str
    glpi_number: str
    full_name: str
    taxpayer_identification: str
    national_identification: str
    address: str
    nationality: str
    role: str
    marital_status: str
    cc: str
    manager: str
    business_executive: str
    project: str
    workload: str
    register_number: str
    serial_number: str
    description: str
    accessories: str
    ms_office: str
    pattern: str
    operational_system: str
    value: str
    date: str
    witnesses: List[WitnessContextSchema]
    location: str


class NewLendingPjContextSchema(BaseSchema):
    """Context for contract template"""

    number: str
    glpi_number: str
    full_name: str
    taxpayer_identification: str
    national_identification: str
    company: str
    cnpj: str
    company_address: str
    address: str
    nationality: str
    role: str
    marital_status: str
    cc: str
    manager: str
    business_executive: str
    project: str
    workload: str
    date_confirm: str
    goal: str
    register_number: str
    serial_number: str
    description: str
    accessories: str
    ms_office: str
    pattern: str
    operational_system: str
    value: str
    date: str
    witnesses: List[WitnessContextSchema]
    location: str


class NewLendingTermContextSchema(BaseSchema):
    """Context for contract template"""

    number: str
    glpi_number: str
    full_name: str
    taxpayer_identification: str
    national_identification: str
    address: str
    nationality: str
    role: str
    cc: str
    manager: str
    project: str
    description: str
    size: str
    quantity: int
    value: str
    date: str
    location: str


class UploadSignedContractSchema(BaseSchema):
    """Schema for upload contract signed"""

    lending_id: int = Field(alias="lendingId")


class CreateWitnessSchema(BaseSchema):
    """Create witness schema"""

    employee_id: int = Field(alias="employeeId")
