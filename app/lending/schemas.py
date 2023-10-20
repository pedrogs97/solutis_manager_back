"""Lending schemas"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import Field
from app.schemas import BaseSchema
from app.people.schemas import EmployeeSerializer


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


class AssetTypeTotvsSchema(BaseSchema):
    """
    Asset type schema

    * Computadores e Periféricos
    * Máquinas e equipamentos
    * Móveis e utensilios
    * Veículos
    * Instalações
    * Benfeitorias em Imóveis
    * Softwares Admnistrativos
    """

    code: int
    group_code: str
    name: str


class AssetTypeSerializer(BaseSchema):
    """
    Asset type serializer schema

    * Computadores e Periféricos
    * Máquinas e equipamentos
    * Móveis e utensilios
    * Veículos
    * Instalações
    * Benfeitorias em Imóveis
    * Softwares Admnistrativos
    """

    id: int
    code: int
    group_code: str
    name: str


class AssetStatusSerializer(BaseSchema):
    """
    Asset status serializer scehama

    * Disponível
    * Comodato
    * Estoque SP
    * Estoque BA
    * Reservado
    * Inativo
    * Empréstimo
    * Descarte
    """

    id: int
    name: str


class AssetClothingSizeSerializer(BaseSchema):
    """
    Asset clothing size serializer scehama

    * PP
    * P
    * M
    * G
    * GG
    * XG
    """

    id: int
    name: str


class AssetTotvsSchema(BaseSchema):
    """Asset schema"""

    code: int
    type: str

    # tombo - registro patrimonial
    register_number: str
    description: str
    # fornecedor
    supplier: str
    # garantia
    assurance_date: datetime
    observations: str
    discard_reason: str
    # padrão
    pattern: str
    operational_system: str
    serial_number: str
    imei: str
    acquisition_date: datetime
    value: float
    # pacote office
    ms_office: bool
    line_number: str
    # operadora
    operator: str
    # modelo
    model: str
    # acessórios
    accessories: str
    configuration: str
    # quantidade do  ativo
    quantity: int
    # unidade da quantidade
    unit: str
    active: bool


class AssetSerializer(BaseSchema):
    """Asset serializer schema"""

    id: int
    type: Optional[AssetTypeSerializer] = None
    clothing_size: Optional[AssetClothingSizeSerializer] = Field(
        serialization_alias="taxpayerIdentification",
        default=None,
    )
    status: Optional[AssetStatusSerializer] = None

    # tombo - regiOptional[str]o patrimonial
    register_number: Optional[str] = Field(
        serialization_alias="registerNumber",
        default=None,
    )
    description: Optional[str] = None
    # fornecedor
    supplier: Optional[str] = None
    # garantia
    assurance_date: Optional[date] = Field(
        serialization_alias="assuranceDate",
        default=None,
    )
    observations: Optional[str] = None
    discard_reason: Optional[str] = Field(
        serialization_alias="discardReason",
        default=None,
    )
    # padrão
    pattern: Optional[str] = None
    operational_system: Optional[str] = Field(
        serialization_alias="operationalSystem",
        default=None,
    )
    serial_number: Optional[str] = Field(
        serialization_alias="serialNumber",
        default=None,
    )
    imei: Optional[str] = None
    acquisition_date: Optional[date] = Field(
        serialization_alias="acquisitionDate",
        default=None,
    )
    value: float
    # pacote office
    ms_office: Optional[bool] = Field(
        serialization_alias="msOffice",
        default=None,
    )
    line_number: Optional[str] = Field(
        serialization_alias="lineNumber",
        default=None,
    )
    # operadora
    operator: Optional[str] = None
    # modelo
    model: Optional[str] = None
    # acessórios
    accessories: Optional[str] = None
    configuration: Optional[str] = None
    # quantidade do  ativo
    quantity: Optional[int] = None
    # unidade da quantidade
    unit: Optional[str] = None
    by_agile: bool = Field(
        serialization_alias="byAgile",
        default=False,
    )


class NewAssetSchema(BaseSchema):
    """New asset schema"""

    type: Optional[str] = None
    clothing_size: Optional[str] = Field(
        alias="clothingSize",
        serialization_alias="clothing_size",
        default=None,
    )
    status: Optional[str] = None

    code: Optional[str] = None
    # tombo - regiOptional[str]o patrimonial
    register_number: Optional[str] = Field(
        alias="registerNumber",
        serialization_alias="register_number",
        default=None,
    )
    description: Optional[str] = None
    # fornecedor
    supplier: Optional[str] = None
    # garantia
    assurance_date: Optional[date] = Field(
        alias="assuranceDate",
        serialization_alias="assurance_date",
        default=None,
    )
    observations: Optional[str] = None
    discard_reason: Optional[str] = Field(
        alias="discardReason",
        serialization_alias="discard_reason",
        default=None,
    )
    # padrão
    pattern: Optional[str] = None
    operational_system: Optional[str] = Field(
        alias="operationalSystem",
        serialization_alias="operational_system",
        default=None,
    )
    serial_number: Optional[str] = Field(
        alias="serialNumber",
        serialization_alias="serial_number",
        default=None,
    )
    imei: Optional[str] = None
    acquisition_date: Optional[date] = Field(
        alias="acquisitionDate",
        serialization_alias="acquisition_date",
        default=None,
    )
    value: float
    # pacote office
    ms_office: Optional[bool] = Field(
        alias="msOffice",
        serialization_alias="ms_office",
        default=None,
    )
    line_number: Optional[str] = Field(
        alias="lineNumber",
        serialization_alias="line_number",
        default=None,
    )
    # operadora
    operator: Optional[str] = None
    # modelo
    model: Optional[str] = None
    # acessórios
    accessories: Optional[str] = None
    configuration: Optional[str] = None
    # quantidade do  ativo
    quantity: Optional[int] = None
    # unidade da quantidade
    unit: Optional[str] = None


class UpdateAssetSchema(BaseSchema):
    """Update asset schema"""

    observations: Optional[str] = None


class InactivateAssetSchema(BaseSchema):
    """Inactivate asset schema"""

    active: bool


class DocumentTemplateSerializerSchema(BaseSchema):
    """Document template serializer schema"""

    id: int
    path: Optional[str]
    file_name: str


class DocumentTypeSerializerSchema(BaseSchema):
    """Document type serializer schema"""

    id: int
    name: str
    doc_template: DocumentTemplateSerializerSchema


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
    employee: EmployeeSerializer
    signed: str


class LendingSerializerSchema(BaseSchema):
    """Lending serializer schema"""

    id: int
    employee: EmployeeSerializer
    asset: AssetSerializer
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


class MaintenanceActionSchema(BaseSchema):
    """Maintenance action schema"""

    id: Optional[int]
    name: str


class MaintenanceStatusSchema(BaseSchema):
    """Maintenance status schema"""

    id: Optional[int]
    name: str


class MaintenanceSchema(BaseSchema):
    """Maintenance schema"""

    id: Optional[int]
    action: str
    status: MaintenanceStatusSchema
    open_date: date
    close_date: Optional[date]
    glpi_number: Optional[str]
    supplier_service_order: Optional[str]
    supplier_number: Optional[str]
    resolution: Optional[str]


class MaintenanceAttachmentSchema(BaseSchema):
    """Maintenance attachment schema"""

    id: Optional[int]
    maintenance: MaintenanceSchema
    path: Optional[str]
    file_name: str


class UpgradeSchema(BaseSchema):
    """Upgrade schema"""

    id: Optional[int]
    status: MaintenanceStatusSchema
    open_date: date
    close_date: Optional[date]
    glpi_number: Optional[str]
    detailing: Optional[str]
    supplier: Optional[str]
    observations: Optional[str]


class VerificationSchema(BaseSchema):
    """Verification schema"""

    id: Optional[int]
    question: str


class VerificationTypeSchema(BaseSchema):
    """
    Verification type schema

    * Saída - envio para o colaborador
    * Retorno - envio para a empresa
    """

    id: Optional[int]
    name: str


class VerificationAnswerSchema(BaseSchema):
    """Verification answer schema"""

    id: Optional[int]
    lending: int
    verification: VerificationSchema
    type: VerificationTypeSchema
    step: str
    answer: str


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
    nacional_identification: str
    address: str
    nationality: str
    role: str
    matrimonial_status: str
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
    nacional_identification: str
    company: str
    cnpj: str
    company_address: str
    address: str
    nationality: str
    role: str
    matrimonial_status: str
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
