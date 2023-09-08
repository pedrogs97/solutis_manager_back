"""Employee models"""
from sqlalchemy import Column, Integer, String, Date
from datasync.models.base import Base
from datasync.schemas.employee import (
    EmployeeSchema,
    EmployeeGenderSchema,
    EmployeeMatrimonialStatusSchema,
    EmployeeNationalitySchema,
)


class EmployeeMatrimonialStatusModel(Base):
    """
    Matrimonial status model

    * C - Casado
    * D - Desquitado
    * E - Uniao Estável
    * I - Divorciado
    * O - Outros
    * P - Separado
    * S - Solteiro
    * V - Viúvo
    """

    __tablename__ = "matrimonial_status"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String, nullable=False)
    description = Column("description", String, nullable=False)

    def to_schema(self):
        """Return model schema"""
        return EmployeeMatrimonialStatusSchema(
            Id=self.id, Code=self.code, Description=self.description
        )

    def __str__(self):
        return f"{self.description}"


class EmployeeGenderModel(Base):
    """
    Gender model

    * M - Masculino
    * F - Femino
    """

    __tablename__ = "gender"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String, nullable=False)
    description = Column("description", String, nullable=False)

    def to_schema(self):
        """Return model schema"""
        return EmployeeGenderSchema(
            Id=self.id, Code=self.code, Description=self.description
        )

    def __str__(self):
        return f"{self.description}"


class EmployeeNationalityModel(Base):
    """
    Nationality model

    All countries
    """

    __tablename__ = "nationality"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String, nullable=False)
    description = Column("description", String, nullable=False)

    def to_schema(self):
        """Return model schema"""
        return EmployeeNationalitySchema(
            Id=self.id, Code=self.code, Description=self.description
        )

    def __str__(self):
        return f"{self.description}"


class EmployeeModel(Base):
    """Employee model"""

    __tablename__ = "employees"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", Integer, nullable=False, unique=True)
    full_name = Column("full_name", String, nullable=False)
    taxpayer_identification = Column(
        "taxpayer_identification", String, nullable=False, unique=True
    )
    nacional_identification = Column("nacional_identification", String, nullable=False)
    nationality = Column("nationality", String, nullable=False)
    marital_status = Column("marital_status", String, nullable=False)
    role = Column("role", String, nullable=True)
    manager = Column("manager", String, nullable=True)
    address = Column("address", String, nullable=False)
    cell_phone = Column("cell_phone", String, nullable=False)
    email = Column("email", String, nullable=False)
    cost_center_number = Column("cost_center_number", String, nullable=True)
    cost_center_name = Column("cost_center_name", String, nullable=True)
    gender = Column("gender", String, nullable=False)
    birthday = Column("birthday", Date, nullable=False)

    def to_schema(self) -> EmployeeSchema:
        """Return model schema"""
        return EmployeeSchema(
            Id=self.id,
            Code=self.code,
            FullName=self.full_name,
            Birthday=self.birthday,
            MaritalStatus=self.marital_status,
            Gender=self.gender,
            Nationality=self.nationality,
            Address=self.address,
            TaxpayerIdentification=self.taxpayer_identification,
            CellPhone=self.cell_phone,
            NacionalIdentification=self.nacional_identification,
            Email=self.email,
            Role=self.role,
            Manager=self.manager,
            CostCenterNumber=self.cost_center_number,
            CostCenterName=self.cost_center_name,
        )

    def __str__(self) -> str:
        return f"{self.code} - {self.full_name}"
