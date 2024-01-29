"""Asset models"""
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from src.database import Base
from src.invoice.models import InvoiceAssets


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

    __tablename__ = "asset_type"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    code = Column("code", String(length=25), nullable=False, unique=True)
    group_code = Column("group_code", String(length=150), nullable=False)
    name = Column("name", String(length=150), nullable=False)
    acronym = Column("acronym", String(length=3), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.acronym} - {self.name}"


class AssetStatusModel(Base):
    """
    Asset status model

    * Disponível
    * Comodato
    * Estoque SP
    * Estoque BA
    * Reservado
    * Inativo
    * Empréstimo
    * Descarte
    """

    __tablename__ = "asset_status"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=20), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class AssetClothingSizeModel(Base):
    """
    Asset clothing size model

    * PP
    * P
    * M
    * G
    * GG
    * XG
    """

    __tablename__ = "asset_clothing_size"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=5), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class AssetModel(Base):
    """Asset model"""

    __tablename__ = "asset"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    type: Mapped[AssetTypeModel] = relationship()
    type_id = Column("type_id", ForeignKey("asset_type.id"), nullable=False)

    status_id = Column(
        "status_id", ForeignKey("asset_status.id"), nullable=True, default=1
    )
    status: Mapped[AssetStatusModel] = relationship()

    clothing_size_id = Column(
        "clothing_size_id", ForeignKey("asset_clothing_size.id"), nullable=True
    )
    clothing_size: Mapped[AssetClothingSizeModel] = relationship()

    invoice: Mapped[InvoiceAssets] = relationship(viewonly=True, uselist=False)

    code = Column("code", String(length=255), nullable=True, unique=True)
    # tombo - registro patrimonial
    register_number = Column("register_number", String(length=255), nullable=True)
    description = Column("description", String(length=255), nullable=True)
    # fornecedor
    supplier = Column("supplier", String(length=100), nullable=True)
    assurance_date = Column("assurance_date", String(length=150), nullable=True)
    observations = Column("observations", String(length=999), nullable=True)
    discard_reason = Column("discard_reason", String(length=255), nullable=True)
    # padrão
    pattern = Column("pattern", String(length=100), nullable=True)
    operational_system = Column("operational_system", String(length=100), nullable=True)
    serial_number = Column("serial_number", String(length=255), nullable=True)
    imei = Column("imei", String(length=255), nullable=True)
    acquisition_date = Column("acquisition_date", DateTime, nullable=True)
    value = Column("value", Float, nullable=True)
    # pacote office
    ms_office = Column("ms_office", Boolean, nullable=True)
    line_number = Column("line_number", String(length=20), nullable=True)
    # operadora
    operator = Column("operator", String(length=50), nullable=True)
    # modelo
    model = Column("model", String(length=100), nullable=True)
    # acessórios
    accessories = Column("accessories", String(length=255), nullable=True)
    configuration = Column("configuration", String(length=255), nullable=True)
    quantity = Column("quantity", Integer, nullable=True, default=1)
    unit = Column("unit", String(length=10), nullable=True)
    active = Column("active", Boolean, nullable=True, default=True)
    by_agile = Column("by_agile", Boolean, nullable=True, default=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.code} - {self.description}"
