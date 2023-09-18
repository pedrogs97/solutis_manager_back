"""
Base schemas
"""
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


class CostCenterSchema(BaseSchema):
    """Cost center schema"""

    id: Optional[int] = None
    code: str
    name: str
    classification: str


class AssetTypeSchema(BaseSchema):
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

    id: Optional[int] = None
    code: int
    group_code: str
    name: str


class AssetStatusSchema(BaseSchema):
    """
    Asset status schema

    * Disponível
    * Comodato
    * Estoque SP
    * Estoque BA
    * Reservado
    * Inativo
    * Empréstimo
    * Descarte
    """

    id: Optional[int] = None
    name: str


class AssetClothingSizeSchema(BaseSchema):
    """
    Asset clothing size schema

    * PP
    * P
    * M
    * G
    * GG
    * XG
    """

    id: Optional[int] = None
    name: str


class AssetSchema(BaseSchema):
    """Asset schema"""

    id: Optional[int] = None
    code: str
    type: AssetTypeSchema
    status: AssetStatusSchema
    clothing_size: Optional[AssetClothingSizeSchema] = None
    cost_center: CostCenterSchema

    # tombo - registro patrimonial
    register_number: str
    description: str
    # fornecedor
    supplier: Optional[str] = None
    # garantia
    assurance_date: Optional[str] = None
    observations: Optional[str] = None
    discard_reason: Optional[str] = None
    # padrão
    pattern: Optional[str] = None
    operational_system: Optional[str] = None
    serial_number: Optional[str] = None
    imei: Optional[str] = None
    acquisition_date: datetime
    value: float
    # pacote office
    ms_office: Optional[bool]
    line_number: Optional[str] = None
    # operadora
    operator: Optional[str] = None
    # modelo
    model: Optional[str] = None
    # acessórios
    accessories: Optional[str] = None
    # quantidade do  ativo
    quantity: int
    # unidade da quantidade
    unit: Optional[str] = None


class EmployeeMatrimonialStatusSchema(BaseSchema):
    """
    Matrimonial status schema

    * C - Casado
    * D - Desquitado
    * E - Uniao Estável
    * I - Divorciado
    * O - Outros
    * P - Separado
    * S - Solteiro
    * V - Viúvo
    """

    id: Optional[int] = None
    code: str
    description: str


class EmployeeGenderSchema(BaseSchema):
    """
    Gender schema

    * M - Masculino
    * F - Femino
    """

    id: Optional[int] = None
    code: str
    description: str


class EmployeeNationalitySchema(BaseSchema):
    """
    Nationality schema

    All countries
    """

    id: Optional[int] = None
    code: str
    description: str


class EmployeeSchema(BaseSchema):
    """Employee schema"""

    id: Optional[int] = None
    code: int
    full_name: str
    birthday: date
    taxpayer_identification: str
    nacional_identification: str
    nationality: str
    marital_status: str
    role: str
    manager: str
    address: str
    cell_phone: str
    email: str
    cost_center_number: str
    cost_center_name: str
    gender: str
