"""Lending schemas"""

from typing import Dict, List, Optional

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


# Lending


class NewLendingDocSchema(BaseSchema):
    """New contract info schema"""

    lending_id: int = Field(alias="lendingId")
    legal_person: bool = Field(alias="legalPerson", default=False)


class RecrateLendingDocSchema(BaseSchema):
    """Recrate contract info schema"""

    lending_id: int = Field(alias="lendingId")
    document_id: Optional[int] = Field(alias="documentId", default=None)
    type: str = "revoke"
    principal_signer: str = Field(alias="principalSigner")
    employee_signer: str = Field(alias="employeeSigner")


class NewRevokeContractDocSchema(BaseSchema):
    """New contract info schema"""

    lending_id: int = Field(alias="lendingId")
    legal_person: bool = Field(alias="legalPerson", default=False)
    witnesses_id: Optional[List[int]] = Field(alias="witnessesId", default=[])
    principal_signer: str = Field(alias="principalSigner")
    employee_signer: str = Field(alias="employeeSigner")


class WitnessContextSchema(BaseSchema):
    """Witness context for template"""

    full_name: str
    taxpayer_identification: str


class VerificationContextSchema(BaseSchema):
    """Verification context for template"""

    number: str
    verifications: List[dict]


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
    manager: Optional[str] = None
    business_executive: str
    project: str
    workload: str
    detail: List[dict]
    date: str
    witnesses: List[WitnessContextSchema]
    location: str
    bu: str
    verifications: Optional[List[Dict]] = None
    attachments_files: Optional[List[Dict]] = None


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
    bu: str
    verifications: Optional[List[Dict]] = None
    attachments_files: Optional[List[Dict]] = None


# TERM


class NewTermDocSchema(BaseSchema):
    """New term info schema"""

    term_id: int = Field(alias="termId")
    legal_person: bool = Field(alias="legalPerson", default=False)
    # principal_signer: str = Field(alias="principalSigner")
    # employee_signer: str = Field(alias="employeeSigner")


class NewRevokeTermDocSchema(BaseSchema):
    """New term info schema"""

    term_id: int = Field(alias="termId")
    principal_signer: str = Field(alias="principalSigner")
    employee_signer: str = Field(alias="employeeSigner")


class NewTermContextSchema(BaseSchema):
    """Context for term template"""

    number: str
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
    location: str


class SignLendingDocSchema(BaseSchema):
    """Sign lending document schema"""

    document_id: int = Field(alias="documentId")
