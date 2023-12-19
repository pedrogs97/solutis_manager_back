"""People models"""
from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from src.database import Base


class CostCenterModel(Base):
    """Cost center model"""

    __tablename__ = "cost_center"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=25), nullable=False, unique=True)
    name = Column("name", String(length=60), nullable=False)
    classification = Column("group_name", String(length=60), nullable=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.code}"


class EmployeeMaritalStatusModel(Base):
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

    __tablename__ = "marital_status"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=1), nullable=False, unique=True)
    description = Column("description", String(length=50), nullable=False)

    def __str__(self):
        return f"{self.description}"


class EmployeeGenderModel(Base):
    """
    Gender model

    * M - Masculino
    * F - Feminino
    """

    __tablename__ = "genders"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=1), nullable=False, unique=True)
    description = Column("description", String(length=50), nullable=False)

    def __str__(self):
        return f"{self.description}"


class EmployeeNationalityModel(Base):
    """
    Nationality model

    All countries
    """

    __tablename__ = "nationalities"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=3), nullable=False, unique=True)
    description = Column("description", String(length=50), nullable=False)

    def __str__(self):
        return f"{self.description}"


class EmployeeRoleModel(Base):
    """Employee role model"""

    __tablename__ = "employee_roles"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=10), nullable=False, unique=True)
    name = Column("name", String(length=100), nullable=False)


class EmployeeModel(Base):
    """Employee model"""

    __tablename__ = "employees"
    __allow_unmapped__ = True

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    role: Mapped[EmployeeRoleModel] = relationship()
    role_id = Column("role_id", ForeignKey(EmployeeRoleModel.id), nullable=True)

    nationality: Mapped[EmployeeNationalityModel] = relationship()
    nationality_id = Column(
        "nationality_id", ForeignKey(EmployeeNationalityModel.id), nullable=True
    )

    marital_status: Mapped[EmployeeMaritalStatusModel] = relationship()
    marital_status_id = Column(
        "marital_status_id",
        ForeignKey(EmployeeMaritalStatusModel.id),
        nullable=True,
    )

    gender: Mapped[EmployeeGenderModel] = relationship()
    gender_id = Column("gender_id", ForeignKey(EmployeeGenderModel.id), nullable=False)

    code = Column("code", String(length=10), nullable=True, unique=True)
    status = Column("status", String(length=100), default="Ativo")
    full_name = Column("full_name", String(length=120), nullable=False)
    taxpayer_identification = Column(
        "taxpayer_identification", String(length=11), nullable=False, unique=True
    )
    national_identification = Column(
        "national_identification", String(length=15), nullable=False
    )
    address = Column("address", String(length=255), nullable=False)
    cell_phone = Column("cell_phone", String(length=15), nullable=False)
    email = Column("email", String(length=60), nullable=False)
    birthday = Column("birthday", Date, nullable=False)
    manager = Column("manager", String(length=150), nullable=True)
    legal_person = Column("legal_person", Boolean, nullable=False, default=False)
    employer_number = Column("employer_number", String(length=255), nullable=True)
    employer_address = Column("employer_address", String(length=255), nullable=True)
    employer_name = Column("employer_name", String(length=255), nullable=True)

    def __str__(self) -> str:
        return f"{self.code} - {self.full_name}"
