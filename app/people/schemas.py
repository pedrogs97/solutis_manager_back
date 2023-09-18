"""People schemas"""
from typing import Optional
from datetime import date
from app.schemas import BaseSchema


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

    id: Optional[int]
    code: str
    description: str


class EmployeeGenderSchema(BaseSchema):
    """
    Gender schema

    * M - Masculino
    * F - Femino
    """

    id: Optional[int]
    code: str
    description: str


class EmployeeNationalitySchema(BaseSchema):
    """
    Nationality schema

    All countries
    """

    id: Optional[int]
    code: str
    description: str


class EmployeeSchema(BaseSchema):
    """Employee schema"""

    id: Optional[int]
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
