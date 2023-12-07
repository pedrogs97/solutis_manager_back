"""Datasync schemas"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


class BaseTotvsSchema(BaseSchema):
    """Totvs base schema"""

    code: str


class CostCenterTotvsSchema(BaseTotvsSchema):
    """Cost center schema"""

    name: str
    classification: str


class AssetTypeTotvsSchema(BaseTotvsSchema):
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

    group_code: str
    name: str


class AssetTotvsSchema(BaseTotvsSchema):
    """Asset schema"""

    type: str
    cost_center: Optional[str] = ""
    active: bool
    # tombo - registro patrimonial
    register_number: str
    description: str
    # fornecedor
    supplier: str
    # garantia
    assurance_date: Optional[datetime]
    observations: str
    discard_reason: str = ""
    # padrão
    pattern: str
    operational_system: str
    serial_number: str
    imei: str
    acquisition_date: Optional[datetime]
    value: float
    # pacote office
    ms_office: bool
    line_number: str
    # operadora
    operator: str
    # modelo
    model: str = ""
    # acessórios
    accessories: str
    # quantidade do  ativo
    unit: str
    # unidade da quantidade
    quantity: int


class EmployeeMatrialStatusTotvsSchema(BaseTotvsSchema):
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

    description: str


class EmployeeGenderTotvsSchema(BaseTotvsSchema):
    """
    Gender schema

    * M - Masculino
    * F - Femino
    """

    description: str


class EmployeeNationalityTotvsSchema(BaseTotvsSchema):
    """
    Nationality schema

    All countries
    """

    description: str


class EmployeeRoleTotvsSchema(BaseTotvsSchema):
    """Employee role schema"""

    name: str


class EmployeeTotvsSchema(BaseTotvsSchema):
    """Employee schema"""

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
