"""Lending schemas"""
from typing import Optional, List
from datetime import datetime, date
from app.schemas import BaseSchema
from app.people.schemas import EmployeeTotvsSchema


class AssetTypeTotvsSchema(BaseSchema):
    """
    Asset type

    * Desktop
    * Notebook
    * Monitor
    * Impressora
    * Tablet
    * Telefonia
    * Webcam
    * Pendrive
    * Mobiliário
    * Kit Mouse e Teclado
    * Teclado
    * Kit Ferramentas
    * Headset
    * HD Externo
    * Fardamento
    * Chip
    """

    id: Optional[int]
    name: str


class AssetStatusSchema(BaseSchema):
    """
    Asset status scehama

    * Disponível
    * Comodato
    * Estoque SP
    * Estoque BA
    * Reservado
    * Inativo
    * Empréstimo
    * Descarte
    """

    id: Optional[int]
    name: str


class AssetClothingSizeSchema(BaseSchema):
    """
    Asset clothing size scehama

    * PP
    * P
    * M
    * G
    * GG
    * XG
    """

    id: Optional[int]
    name: str


class AssetTotvsSchema(BaseSchema):
    """Asset schema"""

    id: Optional[int]
    type: AssetTypeTotvsSchema
    status: AssetStatusSchema
    clothing_size: AssetClothingSizeSchema
    # tombo - registro patrimonial
    register_number: Optional[str]
    description: Optional[str]
    # fornecedor
    supplier: Optional[str]
    assurance_date: Optional[str]
    observations: Optional[str]
    discard_reason: Optional[str]
    # padrão
    pattern: Optional[str]
    operational_system: Optional[str]
    serial_number: Optional[str]
    imei: Optional[str]
    acquisition_date: Optional[datetime]
    value: Optional[float]
    # pacote office
    ms_office: bool
    line_number: Optional[str]
    # operadora
    operator: Optional[str]
    # modelo
    model: Optional[str]
    # acessórios
    accessories: Optional[str]
    configuration: Optional[str]


class DocumentTypeSchema(BaseSchema):
    """Document type schema"""

    id: Optional[int]
    name: str


class DocumentTemplateSchema(BaseSchema):
    """Document template schema"""

    id: Optional[int]
    type: DocumentTypeSchema
    path: Optional[str]
    file_name: str
    content: str


class DocumentSchema(BaseSchema):
    """Document schema"""

    id: Optional[int]
    doc_template: DocumentTemplateSchema
    path: Optional[str]
    file_name: str
    number: str


class WorkloadSchema(BaseSchema):
    """Workload schema"""

    id: Optional[int]
    name: str


class WitnessSchema(BaseSchema):
    """Witness schema"""

    id: Optional[int]
    employee: EmployeeTotvsSchema
    signed: date


class CostCenterTotvsSchema(BaseSchema):
    """Witness schema"""

    id: Optional[int]
    code: str
    name: str


class LendingSchema(BaseSchema):
    """Lending schema"""

    id: Optional[int]
    employee: EmployeeTotvsSchema
    asset: AssetTotvsSchema
    document: DocumentSchema
    workload: WorkloadSchema
    witnesses: List[WitnessSchema]
    cost_center: CostCenterTotvsSchema
    manager: str
    observation: Optional[str]
    signed_date: date
    glpi_number: Optional[str]


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
    lending: LendingSchema
    verification: VerificationSchema
    type: VerificationTypeSchema
    step: str
    answer: str
