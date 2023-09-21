"""
Base schemas
"""
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


class CostCenterTotvsSchema(BaseSchema):
    """Cost center schema"""

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


class AssetTotvsSchema(BaseSchema):
    """Asset schema"""

    code: Optional[int]
    type: Optional[str]
    clothing_size: Optional[str] = None
    cost_center: Optional[str]

    # tombo - registro patrimonial
    register_number: Optional[str]
    description: Optional[str]
    # fornecedor
    supplier: Optional[str] = None
    # garantia
    assurance_date: Optional[datetime] = None
    observations: Optional[str] = None
    discard_reason: Optional[str] = None
    # padrão
    pattern: Optional[str] = None
    operational_system: Optional[str] = None
    serial_number: Optional[str] = None
    imei: Optional[str] = None
    acquisition_date: Optional[datetime] = None
    value: Optional[float]
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
    quantity: Optional[int] = None
    # unidade da quantidade
    unit: Optional[str] = None
    active: Optional[bool] = None


class EmployeeMatrimonialStatusTotvsSchema(BaseSchema):
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

    code: str
    description: str


class EmployeeGenderTotvsSchema(BaseSchema):
    """
    Gender schema

    * M - Masculino
    * F - Femino
    """

    code: str
    description: str


class EmployeeNationalityTotvsSchema(BaseSchema):
    """
    Nationality schema

    All countries
    """

    code: str
    description: str


class EmployeeRoleTotvsSchema(BaseSchema):
    """Employee role schema"""

    code: str
    name: str


class EmployeeTotvsSchema(BaseSchema):
    """Employee schema"""

    code: int
    full_name: str
    birthday: date
    taxpayer_identification: str
    nacional_identification: str
    nationality: str
    marital_status: str
    role: str
    address: str
    cell_phone: str
    email: str
    gender: str
