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


class EmployeeEducationalLevelSerializerSchema(BaseSchema):
    """
    Educational Level serializer schema
    """

    id: int
    description: str
    code: str


class NewEmployeeSchema(BaseSchema):
    """New employee schema"""

    role: int
    nationality_id: int = Field(
        alias="nationalityId",
        serialization_alias="nationality_id",
    )
    marital_status_id: int = Field(
        alias="maritalStatusId",
        serialization_alias="marital_status_id",
    )
    gender_id: int = Field(
        alias="genderId",
        serialization_alias="gender_id",
    )

    educational_level_id: int = Field(
        alias="educationalLevelId",
        serialization_alias="educational_level_id",
    )

    registration: Optional[str] = None
    code: Optional[int] = None
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
    employer_contract_object: Optional[str] = Field(
        alias="employerContractObject",
        default=None,
    )
    employer_contract_date: Optional[date] = Field(
        alias="employerContractDate",
        default=None,
    )
    employer_name: Optional[str] = Field(
        alias="employerName",
        default=None,
    )


class UpdateEmployeeSchema(BaseSchema):
    """Update employee schema"""

    role: Optional[int] = None
    nationality_id: Optional[int] = Field(
        alias="nationalityId",
        serialization_alias="nationality_id",
        default=None,
    )
    marital_status_id: Optional[int] = Field(
        alias="maritalStatusId",
        serialization_alias="marital_status_id",
        default=None,
    )
    gender_id: Optional[int] = Field(
        alias="genderId",
        serialization_alias="gender_id",
        default=None,
    )

    educational_level_id: Optional[int] = Field(
        alias="educationalLevelId",
        serialization_alias="educational_level_id",
        default=None,
    )
    registration: Optional[str] = None
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
    employer_contract_object: Optional[str] = Field(
        alias="employerContractObject",
        default=None,
    )
    employer_contract_date: Optional[date] = Field(
        alias="employerContractDate",
        default=None,
    )
    employer_name: Optional[str] = Field(
        alias="employerName",
        default=None,
    )


class EmployeeSerializerSchema(BaseSchema):
    """Employee serializer schema"""

    id: int
    role: Optional[EmployeeRoleSerializerSchema]
    nationality: EmployeeNationalitySerializerSchema
    marital_status: EmployeeMatrimonialStatusSerializerSchema = Field(
        serialization_alias="maritalStatus"
    )
    gender: EmployeeGenderSerializerSchema
    educational_level: Optional[EmployeeEducationalLevelSerializerSchema] = Field(
        serialization_alias="educationalLevel", default=None
    )
    code: Optional[str] = None
    status: str
    full_name: str = Field(serialization_alias="fullName")
    taxpayer_identification: str = Field(serialization_alias="taxpayerIdentification")
    national_identification: str = Field(serialization_alias="nationalIdentification")
    address: str
    cell_phone: str = Field(serialization_alias="cellPhone")
    email: str
    birthday: str
    manager: Optional[str] = None
    registration: Optional[str] = None
    admission_date: Optional[str] = Field(serialization_alias="admissionDate")
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
    employer_contract_object: Optional[str] = Field(
        serialization_alias="employerContractObject",
        default=None,
    )
    employer_contract_date: Optional[str] = Field(
        serialization_alias="employerContractDate",
        default=None,
    )


class EmployeeShortSerializerSchema(BaseSchema):
    """Employee short serializer schema"""

    id: int
    code: Optional[str] = None
    full_name: str = Field(serialization_alias="fullName")
    registration: Optional[str] = None


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
