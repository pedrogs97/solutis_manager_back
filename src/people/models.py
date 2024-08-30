"""People models"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, relationship

from src.database import Base
from src.datasync.models import (
    EmployeeEducationalLevelTOTVSModel,
    EmployeeGenderTOTVSModel,
    EmployeeMaritalStatusTOTVSModel,
    EmployeeNationalityTOTVSModel,
    EmployeeRoleTOTVSModel,
)


class EmployeeModel(Base):
    """Employee model"""

    __tablename__ = "employees"
    __allow_unmapped__ = True

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    user: Mapped["UserModel"] = relationship(viewonly=True)

    role: Mapped[EmployeeRoleTOTVSModel] = relationship()
    role_id = Column("role_id", ForeignKey(EmployeeRoleTOTVSModel.id), nullable=True)

    nationality: Mapped[EmployeeNationalityTOTVSModel] = relationship()
    nationality_id = Column(
        "nationality_id", ForeignKey(EmployeeNationalityTOTVSModel.id), nullable=True
    )

    marital_status: Mapped[EmployeeMaritalStatusTOTVSModel] = relationship()
    marital_status_id = Column(
        "marital_status_id",
        ForeignKey(EmployeeMaritalStatusTOTVSModel.id),
        nullable=True,
    )

    gender: Mapped[EmployeeGenderTOTVSModel] = relationship()
    gender_id = Column(
        "gender_id", ForeignKey(EmployeeGenderTOTVSModel.id), nullable=False
    )

    educational_level: Mapped[EmployeeEducationalLevelTOTVSModel] = relationship()
    educational_level_id = Column(
        "educational_level_id",
        ForeignKey(EmployeeEducationalLevelTOTVSModel.id),
        nullable=True,
    )

    job_position = Column("job_position", String(200), nullable=True)

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
    admission_date = Column("admission_date", Date, nullable=True)
    registration = Column("registration", String(length=16), nullable=True)
    # PJ
    legal_person = Column("legal_person", Boolean, nullable=False, default=False)
    # CNPJ
    employer_number = Column("employer_number", String(length=255), nullable=True)
    employer_address = Column("employer_address", String(length=255), nullable=True)
    employer_name = Column("employer_name", String(length=255), nullable=True)
    employer_contract_object = Column(
        "employer_contract_object", String(length=255), nullable=True
    )
    employer_contract_date = Column("employer_contract_date", Date, nullable=True)
    employer_end_contract_date = Column(
        "employer_end_contract_date", Date, nullable=True
    )
    created_at = Column(
        "created_at", DateTime, nullable=False, server_default=func.now()
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    def __str__(self) -> str:
        return f"{self.code} - {self.full_name}"
