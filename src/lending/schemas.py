"""Lending schemas"""
from datetime import date
from typing import List, Optional

from pydantic import Field

from src.asset.schemas import AssetSerializerSchema
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
    signed: str


class LendingSerializerSchema(BaseSchema):
    """Lending serializer schema"""

    id: int
    employee: EmployeeSerializerSchema
    asset: AssetSerializerSchema
    document: int
    workload: WorkloadSerializerSchema
    witnesses: List[WitnessSerializerSchema]
    cost_center: CostCenterSerializerSchema = Field(serialization_alias="costCenter")
    manager: str
    observations: Optional[str]
    signed_date: str = Field(serialization_alias="signedDate")
    glpi_number: Optional[str] = Field(serialization_alias="glpiNumber")


class NewLendingSchema(BaseSchema):
    """New lending schema"""

    employee_id: int = Field(alias="employeeId")
    asset_id: int = Field(alias="assetId")
    document_id: Optional[int] = Field(alias="documentId", default=None)
    workload_id: int = Field(alias="workloadId")
    witnesses_id: List[int] = Field(alias="witnessesId")
    cost_center_id: int = Field(alias="costCenterId")
    manager: str
    observations: Optional[str] = None
    signed_date: Optional[date] = Field(alias="signedDate", default=None)
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)


class NewLendingDocSchema(BaseSchema):
    """New contract info schema"""

    number: str
    glpi_number: str = Field(alias="glpiNumber")
    employee_id: int = Field(alias="employeeId")
    asset_id: int = Field(alias="assetId")
    witness1_id: int = Field(alias="witness1Id")
    witness2_id: int = Field(alias="witness2Id")
    lending_id: int = Field(alias="lendingId")
    workload_id: int = Field(alias="workloadId")
    cc: str
    manager: str
    project: str
    business_executive: str = Field(alias="businessExecutive")
    legal_person: bool = Field(alias="legalPerson", default=False)
    date_confirm: Optional[str] = Field(alias="dateConfirm", default=None)
    goal: Optional[str] = Field(alias="goal", default=None)
    project: Optional[str] = None


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


class UploadSignedContractSchema(BaseSchema):
    """Schema for upload contract signed"""

    lending_id: int = Field(alias="lendingId")
    document_id: int = Field(alias="documentId")
