"""Datasync models"""
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, func

from src.config import DATE_FORMAT
from src.database import Base


class CostCenterTOTVSModel(Base):
    """Cost center model"""

    __tablename__ = "cost_centers_totvs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=25), nullable=False, unique=True)
    name = Column("name", String(length=60), nullable=False)
    classification = Column("group_name", String(length=60), nullable=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.code}"


class AssetTypeTOTVSModel(Base):
    """
    Asset type model

    * Computadores e Periféricos
    * Máquinas e equipamentos
    * Móveis e utensilios
    * Veículos
    * Instalações
    * Benfeitorias em Imóveis
    * Softwares Admnistrativos
    """

    __tablename__ = "asset_types_totvs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=10), nullable=False, unique=True)
    group_code = Column("group_name", String(length=10), nullable=False)
    name = Column("name", String(length=40), nullable=False)

    def __str__(self):
        return f"{self.name} - {self.group_code}"


class AssetTOTVSModel(Base):
    """Asset model"""

    __tablename__ = "assets_totvs"
    __allow_unmapped__ = True

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=10), unique=True, nullable=False)

    type = Column("type", String(length=100), nullable=False)

    cost_center = Column("cost_center", String(length=150), nullable=True, default="")

    active = Column("active", Boolean, nullable=True)
    # tombo - registro patrimonial
    register_number = Column("register_number", String(length=30), nullable=True)
    description = Column("description", String(length=240), nullable=True)
    # fornecedor
    supplier = Column("supplier", String(length=100), nullable=True)
    assurance_date = Column("assurance_date", DateTime, nullable=True)
    observations = Column("observations", String(length=999), nullable=True)
    discard_reason = Column("discard_reason", String(length=255), nullable=True)
    # padrão
    pattern = Column("pattern", String(length=255), nullable=True)
    operational_system = Column("operational_system", String(length=255), nullable=True)
    serial_number = Column("serial_number", String(length=255), nullable=True)
    imei = Column("imei", String(length=255), nullable=True)
    acquisition_date = Column("acquisition_date", DateTime, nullable=True)
    value = Column("value", Float, nullable=True)
    # pacote office
    ms_office = Column("ms_office", Boolean, nullable=True)
    line_number = Column("line_number", String(length=255), nullable=True)
    # operadora
    operator = Column("operator", String(length=255), nullable=True)
    # modelo
    model = Column("model", String(length=255), nullable=True)
    # acessórios
    accessories = Column("accessories", String(length=255), nullable=True)
    unit = Column("unit", String(length=3), nullable=True)
    quantity = Column("quantity", Integer, nullable=True)

    def __str__(self):
        return f"{self.code} - {self.description}"


class EmployeeMaritalStatusTOTVSModel(Base):
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

    __tablename__ = "marital_status_totvs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=1), nullable=False, unique=True)
    description = Column("description", String(length=50), nullable=False)

    def __str__(self):
        return f"{self.code} - {self.description}"


class EmployeeGenderTOTVSModel(Base):
    """
    Gender model

    * M - Masculino
    * F - Femino
    """

    __tablename__ = "genders_totvs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=1), nullable=False, unique=True)
    description = Column("description", String(length=50), nullable=False)

    def __str__(self):
        return f"{self.description}"


class EmployeeNationalityTOTVSModel(Base):
    """
    Nationality model

    All countries
    """

    __tablename__ = "nationalities_totvs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=3), nullable=False, unique=True)
    description = Column("description", String(length=50), nullable=False)

    def __str__(self):
        return f"{self.description}"


class EmployeeRoleTOTVSModel(Base):
    """Employee role model"""

    __tablename__ = "roles_totvs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=10), nullable=False, unique=True)
    name = Column("name", String(length=100), nullable=False)

    def __str__(self):
        return f"{self.code} - {self.name}"


class EmployeeEducationalLevelTOTVSModel(Base):
    """
    Educational Level model

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

    __tablename__ = "educational_totvs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=3), nullable=False, unique=True)
    description = Column("description", String(length=50), nullable=False)

    def __str__(self):
        return f"{self.description}"


class EmployeeTOTVSModel(Base):
    """Employee model"""

    __tablename__ = "employees_totvs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=10), nullable=False, unique=True)
    full_name = Column("full_name", String(length=120), nullable=False)
    taxpayer_identification = Column(
        "taxpayer_identification", String(length=11), nullable=False, unique=True
    )
    national_identification = Column(
        "national_identification", String(length=15), nullable=False
    )
    nationality = Column("nationality", String(length=50), nullable=False)
    marital_status = Column("marital_status", String(length=50), nullable=False)
    role = Column("role", String(length=100), nullable=True)
    status = Column("status", String(length=100), nullable=True)
    address = Column("address", String(length=255), nullable=False)
    cell_phone = Column("cell_phone", String(length=15), nullable=False)
    email = Column("email", String(length=60), nullable=False)
    gender = Column("gender", String(length=50), nullable=False)
    birthday = Column("birthday", Date, nullable=False)
    admission_date = Column("admission_date", Date, nullable=True)
    registration = Column("registration", String(length=16), nullable=True)
    educational_level = Column("education_level", String(length=50), nullable=True)

    def __str__(self) -> str:
        return f"{self.code} - {self.full_name}"


class SyncModel(Base):
    """Sync model"""

    __tablename__ = "syncs_totvs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    updated_at = Column("updated_at", DateTime, server_default=func.now())
    count_new_values = Column("count_new_values", Integer, nullable=False)
    model = Column("model", String(length=50), nullable=True, default="employee")
    execution_time = Column("execution_time", Float, nullable=False)

    def __str__(self):
        datetime_str = datetime.strftime(self.updated_at, DATE_FORMAT)
        return f"{self.model} ({self.count_new_values}) - {datetime_str}"
