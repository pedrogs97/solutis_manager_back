"""People schemas"""
from typing import Optional
from datetime import date
from pydantic import Field
from app.schemas import BaseSchema


class EmployeeMatrimonialStatusSerializer(BaseSchema):
    """
    Matrimonial status serializer schema

    * C - Casado
    * D - Desquitado
    * E - Uniao Estável
    * I - Divorciado
    * O - Outros
    * P - Separado
    * S - Solteiro
    * V - Viúvo
    """

    id: int
    code: str
    description: str


class EmployeeGenderSerializer(BaseSchema):
    """
    Gender serializer schema

    * M - Masculino
    * F - Femino
    """

    id: int
    code: str
    description: str


class EmployeeNationalitySerializer(BaseSchema):
    """
    Nationality serializer schema

    All countries
    """

    id: int
    code: str
    description: str


class EmployeeRoleSerializer(BaseSchema):
    """
    Role serializer schema
    """

    id: int
    code: str
    description: str


class NewEmployeeSchema(BaseSchema):
    """New employee schema"""

    role: str
    nationality: str
    matrimonial_status: str = Field(
        alias="matrimonialStatus",
        serialization_alias="matrimonial_status",
    )
    gender: str
    code: Optional[int] = None
    full_name: str = Field(
        alias="fullName",
        serialization_alias="full_name",
    )
    taxpayer_identification: str = Field(
        alias="taxpayerIdentification",
        serialization_alias="taxpayer_identification",
    )
    nacional_identification: str = Field(
        alias="nacionalIdentification",
        serialization_alias="nacional_identification",
    )
    address: str
    cell_phone: str = Field(
        alias="cellPhone",
        serialization_alias="cell_phone",
    )
    email: str
    birthday: date
    manager: Optional[str] = None


class UpdateEmployeeSchema(BaseSchema):
    """Update employee schema"""

    role: Optional[str] = None
    nationality: Optional[str] = None
    matrimonial_status: Optional[str] = Field(
        alias="matrimonialStatus",
        serialization_alias="matrimonial_status",
        default=None,
    )
    gender: Optional[str] = None
    code: Optional[int] = None
    full_name: Optional[str] = Field(
        alias="fullName", serialization_alias="full_name", default=None
    )
    taxpayer_identification: Optional[str] = Field(
        alias="taxpayerIdentification",
        serialization_alias="taxpayer_identification",
        default=None,
    )
    nacional_identification: Optional[str] = Field(
        alias="nacionalIdentification",
        serialization_alias="nacional_identification",
        default=None,
    )
    address: Optional[str] = None
    cell_phone: Optional[str] = Field(
        alias="cellPhone", serialization_alias="cell_phone", default=None
    )
    email: Optional[str] = None
    birthday: Optional[date] = None
    manager: Optional[str] = None


class EmployeeSerializer(BaseSchema):
    """Employee serializer schema"""

    id: int
    role: EmployeeRoleSerializer
    nationality: EmployeeNationalitySerializer
    matrimonial_status: EmployeeMatrimonialStatusSerializer = Field(
        serialization_alias="marimonialStatus"
    )
    gender: EmployeeGenderSerializer
    code: Optional[int] = None
    full_name: str = Field(serialization_alias="fullName")
    taxpayer_identification: str = Field(serialization_alias="taxpayerIdentification")
    nacional_identification: str = Field(serialization_alias="nacionalIdentification")
    address: str
    cell_phone: str = Field(serialization_alias="cellPhone")
    email: str
    birthday: date
    manager: Optional[str] = None
    legal_person: bool = Field(serialization_alias="legalPerson")


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
    matrimonial_status: str
    role: str
    address: str
    cell_phone: str
    email: str
    gender: str
