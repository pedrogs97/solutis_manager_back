"""Service models"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    Date,
    func,
)

Base = declarative_base()


class CostCenterModel(Base):
    """Cost center model"""

    __tablename__ = "cost_centers"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=25), nullable=False)
    name = Column("name", String(length=60), nullable=False)
    classification = Column("group_name", String(length=60), nullable=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.code}"


class AssetTypeModel(Base):
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

    __tablename__ = "asset_types"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", Integer, nullable=False)
    group_code = Column("group_name", String(length=10), nullable=False)
    name = Column("name", String(length=40), nullable=False)

    def __str__(self):
        return f"{self.name} - {self.group_code}"


class AssetModel(Base):
    """Asset model"""

    __tablename__ = "assets"
    __allow_unmapped__ = True

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", Integer, unique=True, nullable=False)

    type = Column("type", String(length=100), nullable=False)

    cost_center: Column("cost_center", String(length=100), nullable=True)

    active = Column("active", Boolean, nullable=True)
    # tombo - registro patrimonial
    register_number = Column("register_number", String(length=30), nullable=True)
    description = Column("description", String(length=240), nullable=True)
    # fornecedor
    supplier = Column("supplier", String(length=100), nullable=True)
    assurance_date = Column("assurance_date", DateTime, nullable=True)
    observations = Column("observations", String(length=255), nullable=True)
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
    configuration = Column("configuration", String(length=255), nullable=True)


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
        return f"{self.code} - {self.description}"


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

    __tablename__ = "roles"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=10), nullable=False)
    name = Column("name", String(length=100), nullable=False)


class EmployeeModel(Base):
    """Employee model"""

    __tablename__ = "employees"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", Integer, nullable=False, unique=True)
    full_name = Column("full_name", String(length=120), nullable=False)
    taxpayer_identification = Column(
        "taxpayer_identification", String(length=11), nullable=False, unique=True
    )
    nacional_identification = Column(
        "nacional_identification", String(length=15), nullable=False
    )
    nationality = Column("nationality", String(length=50), nullable=False)
    matrimonial_status = Column("matrimonial_status", String(length=50), nullable=False)
    role = Column("role", String(length=100), nullable=True)
    address = Column("address", String(length=255), nullable=False)
    cell_phone = Column("cell_phone", String(length=15), nullable=False)
    email = Column("email", String(length=60), nullable=False)
    gender = Column("gender", String(length=50), nullable=False)
    birthday = Column("birthday", Date, nullable=False)

    def __str__(self) -> str:
        return f"{self.code} - {self.full_name}"


class SyncModel(Base):
    """Sync model"""

    __tablename__ = "syncs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    updated_at = Column("updated_at", DateTime, server_default=func.now())
    count_new_values = Column("count_new_values", Integer, nullable=False)
    model = Column("model", String, nullable=True, default="employee")
    execution_time = Column("execution_time", Float, nullable=False)
