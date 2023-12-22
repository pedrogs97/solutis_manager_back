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

    employee: int
    asset: int
    document: Optional[int] = None
    workload: int
    witnesses: List[int]
    cost_center: int = Field(alias="costCenter")
    manager: str
    observations: Optional[str] = None
    signed_date: Optional[date] = Field(alias="signedDate", default=None)
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)


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


class NewVerificationSchema(BaseSchema):
    """New verification schema"""

    question: str
    step: str
    asset_type_id: int = Field(alias="assetTypeId")


class VerificationSerializerSchema(BaseSchema):
    """Verification serializer schema"""

    id: int
    question: str
    step: str
    asset_type: str = Field(serialization_alias="assetType")


class VerificationTypeSerializerSchema(BaseSchema):
    """
    Verification type serializer schema

    * Saída - envio para o colaborador
    * Retorno - envio para a empresa
    """

    id: int
    name: str


class NewVerificationAnswerSchema(BaseSchema):
    """New verification answer schema"""

    lending_id: int = Field(alias="lendingId")
    verification_id: int = Field(alias="verificationId")
    type_id: int = Field(alias="typeId")
    answer: str
    observations: Optional[str] = None


class VerificationAnswerSerializerSchema(BaseSchema):
    """Verification answer serializer schema"""

    id: int
    lending_id: int = Field(serialization_alias="lendingId")
    verification: VerificationSerializerSchema
    type: VerificationTypeSerializerSchema
    answer: str
    observations: Optional[str] = None


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
