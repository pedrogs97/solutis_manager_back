"""Lending schemas"""

from typing import List, Optional

from pydantic import Field

from src.schemas import BaseSchema


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


class NewLendingDocSchema(BaseSchema):
    """New contract info schema"""

    employee_id: int = Field(alias="employeeId")
    lending_id: int = Field(alias="lendingId")
    legal_person: bool = Field(alias="legalPerson", default=False)


class NewRevokeContractDocSchema(BaseSchema):
    """New contract info schema"""

    lending_id: int = Field(alias="lendingId")
    legal_person: bool = Field(alias="legalPerson", default=False)
    witnesses_id: Optional[List[int]] = Field(alias="witnessesId", default=[])


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
    detail: List[dict]
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
    contract_date: str
    object: str
    detail: List[dict]
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
    detail: List[dict]
    date: str
    location: str
