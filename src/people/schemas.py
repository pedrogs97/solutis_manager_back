"""People schemas"""
from datetime import date
from typing import Optional

from pydantic import Field

from src.schemas import BaseSchema


class EmployeeMatrimonialStatusSerializerSchema(BaseSchema):
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


class EmployeeGenderSerializerSchema(BaseSchema):
    """
    Gender serializer schema

    * M - Masculino
    * F - Femino
    """

    id: int
    code: str
    description: str


class EmployeeNationalitySerializerSchema(BaseSchema):
    """
    Nationality serializer schema

    All countries
    """

    id: int
    code: str
    description: str


class EmployeeRoleSerializerSchema(BaseSchema):
    """
    Role serializer schema
    """

    id: int
    name: str
    code: str


class NewEmployeeSchema(BaseSchema):
    """New employee schema"""

    role: str
    nationality: str
    marital_status: str = Field(
        alias="maritalStatus",
        serialization_alias="marital_status",
    )
    gender: str
    code: Optional[str] = None
    status: Optional[str] = "Ativo"
    full_name: str = Field(
        alias="fullName",
        serialization_alias="full_name",
    )
    taxpayer_identification: str = Field(
        alias="taxpayerIdentification",
        serialization_alias="taxpayer_identification",
    )
    national_identification: str = Field(
        alias="nationalIdentification",
        serialization_alias="national_identification",
    )
    address: str
    cell_phone: str = Field(
        alias="cellPhone",
        serialization_alias="cell_phone",
    )
    email: str
    birthday: date
    manager: Optional[str] = None
    employer_number: Optional[str] = Field(
        alias="employerNumber",
        serialization_alias="employer_number",
        default=None,
    )
    employer_address: Optional[str] = Field(
        alias="employerAddress",
        serialization_alias="employer_address",
        default=None,
    )


class UpdateEmployeeSchema(BaseSchema):
    """Update employee schema"""

    role: Optional[str] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = Field(
        alias="maritalStatus",
        serialization_alias="marital_status",
        default=None,
    )
    gender: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = None
    full_name: Optional[str] = Field(
        alias="fullName", serialization_alias="full_name", default=None
    )
    taxpayer_identification: Optional[str] = Field(
        alias="taxpayerIdentification",
        serialization_alias="taxpayer_identification",
        default=None,
    )
    national_identification: Optional[str] = Field(
        alias="nationalIdentification",
        serialization_alias="national_identification",
        default=None,
    )
    address: Optional[str] = None
    cell_phone: Optional[str] = Field(
        alias="cellPhone", serialization_alias="cell_phone", default=None
    )
    email: Optional[str] = None
    birthday: Optional[date] = None
    manager: Optional[str] = None
    employer_number: Optional[str] = Field(
        alias="employerNumber",
        serialization_alias="employer_number",
        default=None,
    )
    employer_address: Optional[str] = Field(
        alias="employerAddress",
        serialization_alias="employer_address",
        default=None,
    )
    employer_name: Optional[str] = Field(
        alias="employerName",
        serialization_alias="employer_name",
        default=None,
    )


class EmployeeSerializerSchema(BaseSchema):
    """Employee serializer schema"""

    id: int
    role: Optional[EmployeeRoleSerializerSchema]
    nationality: EmployeeNationalitySerializerSchema
    marital_status: EmployeeMatrimonialStatusSerializerSchema = Field(
        serialization_alias="marimonialStatus"
    )
    gender: EmployeeGenderSerializerSchema
    code: Optional[str] = None
    status: str
    full_name: str = Field(serialization_alias="fullName")
    taxpayer_identification: str = Field(serialization_alias="taxpayerIdentification")
    national_identification: str = Field(serialization_alias="nationalIdentification")
    address: str
    cell_phone: str = Field(serialization_alias="cellPhone")
    email: str
    birthday: date
    manager: Optional[str] = None
    legal_person: bool = Field(serialization_alias="legalPerson")
    employer_number: Optional[str] = Field(
        serialization_alias="employerNumber",
        default=None,
    )
    employer_address: Optional[str] = Field(
        serialization_alias="employerAddress",
        default=None,
    )
    employer_name: Optional[str] = Field(
        serialization_alias="employerName",
        default=None,
    )


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
    national_identification: str
    nationality: str
    marital_status: str
    role: str
    address: str
    cell_phone: str
    email: str
    gender: str
