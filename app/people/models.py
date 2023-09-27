"""People models"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped
from app.database import Base


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
    code = Column("code", String(length=1), nullable=False)
    description = Column("description", String(length=50), nullable=False)

    def __str__(self):
        return f"{self.description}"


class EmployeeGenderModel(Base):
    """
    Gender model

    * M - Masculino
    * F - Femino
    """

    __tablename__ = "genders"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=1), nullable=False)
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
    code = Column("code", String(length=3), nullable=False)
    description = Column("description", String(length=50), nullable=False)

    def __str__(self):
        return f"{self.description}"


class EmployeeRoleModel(Base):
    """Employee role model"""

    __tablename__ = "employee_roles"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=10), nullable=False)
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
        "nationality_id", ForeignKey(EmployeeNationalityModel.id), nullable=False
    )

    matrimonial_status: Mapped[EmployeeMatrimonialStatusModel] = relationship()
    marital_status_id = Column(
        "marital_status_id",
        ForeignKey(EmployeeMatrimonialStatusModel.id),
        nullable=False,
    )

    gender: Mapped[EmployeeGenderModel] = relationship()
    gender_id = Column("gender_id", ForeignKey(EmployeeGenderModel.id), nullable=False)

    code = Column("code", Integer, nullable=False, unique=True)
    full_name = Column("full_name", String(length=120), nullable=False)
    taxpayer_identification = Column(
        "taxpayer_identification", String(length=11), nullable=False, unique=True
    )
    nacional_identification = Column(
        "nacional_identification", String(length=15), nullable=False
    )
    address = Column("address", String(length=255), nullable=False)
    cell_phone = Column("cell_phone", String(length=15), nullable=False)
    email = Column("email", String(length=60), nullable=False)
    birthday = Column("birthday", Date, nullable=False)
    manager = Column("manger", String(length=150), nullable=True)
    legal_person = Column("legal_person", Boolean, nullable=False, default=False)

    def __str__(self) -> str:
        return f"{self.code} - {self.full_name}"
