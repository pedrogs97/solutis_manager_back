"""Asset models"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from datasync.models.base import Base


class AssetTypeModel(Base):
    """
    Asset type model

    * Desktop
    * Notebook
    * Monitor
    * Impressora
    * Tablet
    * Telefonia
    * Webcam
    * Pendrive
    * Mobiliário
    * Kit Mouse e Teclado
    * Teclado
    * Kit Ferramentas
    * Headset
    * HD Externo
    * Fardamento
    * Chip
    """

    __tablename__ = "asset_types"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False)

    def __str__(self):
        return f"{self.name}"


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
    name = Column("name", String, nullable=False)

    def __str__(self):
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

    __tablename__ = "asset_clothing_sizes"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False)

    def __str__(self):
        return f"{self.name}"


class AssetModel(Base):
    """Asset model"""

    __tablename__ = "assets"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    type = relationship("AssetTypeModel")
    type_id = Column("type_id", ForeignKey("asset_types.id"), nullable=False)

    status_id = Column("status_id", ForeignKey("asset_status.id"), nullable=False)
    status = relationship("AssetStatusModel")

    clothing_size_id = Column(
        "clothing_size_id", ForeignKey("asset_clothing_sizes.id"), nullable=False
    )
    clothing_size = relationship("AssetClothingSizeModel")

    # tombo - registro patrimonial
    register_number = Column("register_number", String, nullable=True)
    description = Column("description", String, nullable=True)
    # fornecedor
    supplier = Column("supplier", String, nullable=True)
    assurance_date = Column("assurance_date", String, nullable=True)
    observations = Column("observations", String, nullable=True)
    discard_reason = Column("discard_reason", String, nullable=True)
    # padrão
    pattern = Column("pattern", String, nullable=True)
    operational_system = Column("operational_system", String, nullable=True)
    serial_number = Column("serial_number", String, nullable=True)
    imei = Column("imei", String, nullable=True)
    acquisition_date = Column("acquisition_date", DateTime, nullable=True)
    value = Column("value", Float, nullable=True)
    # pacote office
    ms_office = Column("ms_office", Boolean, nullable=True)
    line_number = Column("line_number", String, nullable=True)
    # operadora
    operator = Column("operator", String, nullable=True)
    # modelo
    model = Column("model", String, nullable=True)
    # acessórios
    accessories = Column("accessories", String, nullable=True)
    configuration = Column("configuration", String, nullable=True)
