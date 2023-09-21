"""
Base schemas
"""
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

    code: int
    type: str
    clothing_size: str
    cost_center: str

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
    # quantidade do  ativo
    quantity: int
    # unidade da quantidade
    unit: str
    active: bool


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
