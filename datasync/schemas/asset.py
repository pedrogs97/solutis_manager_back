"""Asset schemas"""
from datetime import datetime
from datasync.schemas.base import BaseSchema


class AssetTypeSchema(BaseSchema):
    """
    Asset type
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

    name: str


class AssetStatusSchema(BaseSchema):
    """
    Asset status scehama
    * Disponível
    * Comodato
    * Estoque SP
    * Estoque BA
    * Reservado
    * Inativo
    * Empréstimo
    * Descarte
    """

    name: str


class AssetClothingSizeSchema(BaseSchema):
    """
    Asset clothing size scehama
    * PP
    * P
    * M
    * G
    * GG
    * XG
    """

    name: str


class AssetSchema(BaseSchema):
    """Asset schema"""

    type: AssetTypeSchema
    status: AssetStatusSchema
    clothing_size: AssetClothingSizeSchema
    # tombo - registro patrimonial
    register_number: str
    description: str
    # fornecedor
    supplier: str
    assurance_date: str
    observations: str
    discard_reason: str
    # padrão
    pattern: str
    operational_system: str
    serial_number: str
    imei: str
    acquisition_date: datetime
    value: float
    # pacote office
    ms_office: bool
    line_number: str
    # operadora
    operator: str
    # modelo
    model: str
    # acessórios
    accessories: str
    configuration: str
