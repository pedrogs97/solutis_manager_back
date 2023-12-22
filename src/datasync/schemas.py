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
    cost_center: Optional[str] = None
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


class EmployeeEducationalLevelTotvsSchema(BaseTotvsSchema):
    """
    Educational level schema

    * 1 - Analfabeto
    * 2 - Até o 5º ano incompleto do ensino fundamental
    * 3 - 5º ano completo do ensino fundamental
    * 4 - Do 6º ao 9º ano do ensino fundamental
    * 5 - Ensino fundamental completo
    * 6 - Ensino médio incompleto
    * 7 - Ensino médio completo
    * 8 - Educação superior incompleto
    * 9 - Educação superior completo
    * A - Pós Grad. incompleto
    * B - Pós Grad. completo
    * C - Mestrado incompleto
    * D - Mestrado completo
    * E - Doutorado incompleto
    * F - Doutorado completo
    * G - Pós Dout.incompleto
    * H - Pós Dout.completo
    """

    description: str


class EmployeeMaritalStatusTotvsSchema(BaseTotvsSchema):
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
    national_identification: str
    nationality: str
    marital_status: str
    role: str
    status: str = "Ativo"
    address: str
    cell_phone: str
    email: str
    gender: str
    admission_date: date
    registration: str
