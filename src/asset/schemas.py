"""Asset schemas"""

from datetime import date, datetime
from typing import Optional

from pydantic import Field

from src.schemas import BaseSchema


class AssetTypeTotvsSchema(BaseSchema):
    """
    Asset type schema

    * Computadores e Periféricos
    * Máquinas e equipamentos
    * Móveis e utensilios
    * Veículos
    * Instalações
    * Benfeitorias em Imóveis
    * Softwares Admnistrativos
    """

    code: int
    group_code: str
    name: str


class AssetTypeSerializerSchema(BaseSchema):
    """
    Asset type serializer schema

    * Computadores e Periféricos
    * Máquinas e equipamentos
    * Móveis e utensilios
    * Veículos
    * Instalações
    * Benfeitorias em Imóveis
    * Softwares Admnistrativos
    """

    id: int
    code: str
    group_code: str = Field(serialization_alias="groupCode")
    name: str


class AssetStatusSerializerSchema(BaseSchema):
    """
    Asset status serializer scehama

    * Disponível
    * Comodato
    * Estoque SP
    * Estoque BA
    * Reservado
    * Inativo
    * Empréstimo
    * Descarte
    """

    id: int
    name: str


class AssetClothingSizeSerializer(BaseSchema):
    """
    Asset clothing size serializer scehama

    * PP
    * P
    * M
    * G
    * GG
    * XG
    """

    id: int
    name: str


class AssetTotvsSchema(BaseSchema):
    """Asset schema"""

    code: int
    type: str

    # tombo - registro patrimonial
    register_number: str
    description: str
    # fornecedor
    supplier: str
    # garantia
    assurance_date: datetime
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
    # quantidade do  ativo
    quantity: int
    # unidade da quantidade
    unit: str
    active: bool


class AssetShortSerializerSchema(BaseSchema):
    """Short asset serializer schema"""

    id: int
    description: Optional[str] = None
    # tombo - registro patrimonial
    register_number: Optional[str] = Field(
        serialization_alias="registerNumber",
        default=None,
    )


class AssetSerializerSchema(BaseSchema):
    """Asset serializer schema"""

    id: int
    type: Optional[AssetTypeSerializerSchema] = None
    clothing_size: Optional[AssetClothingSizeSerializer] = Field(
        serialization_alias="clothingSize",
        default=None,
    )
    status: Optional[AssetStatusSerializerSchema] = None

    invoice_asset_number: Optional[str] = Field(
        serialization_alias="invoiceAssetNumber",
        default=None,
    )

    # tombo - registro patrimonial
    register_number: Optional[str] = Field(
        serialization_alias="registerNumber",
        default=None,
    )
    description: Optional[str] = None
    # fornecedor
    supplier: Optional[str] = None
    # garantia
    assurance_date: Optional[str] = Field(
        serialization_alias="assuranceDate",
        default=None,
    )
    observations: Optional[str] = None
    discard_reason: Optional[str] = Field(
        serialization_alias="discardReason",
        default=None,
    )
    # padrão
    pattern: Optional[str] = None
    operational_system: Optional[str] = Field(
        serialization_alias="operationalSystem",
        default=None,
    )
    serial_number: Optional[str] = Field(
        serialization_alias="serialNumber",
        default=None,
    )
    imei: Optional[str] = None
    acquisition_date: Optional[str] = Field(
        serialization_alias="acquisitionDate",
        default=None,
    )
    value: float
    # pacote office
    ms_office: Optional[bool] = Field(
        serialization_alias="msOffice",
        default=None,
    )
    line_number: Optional[str] = Field(
        serialization_alias="lineNumber",
        default=None,
    )
    # operadora
    operator: Optional[str] = None
    # modelo
    model: Optional[str] = None
    # acessórios
    accessories: Optional[str] = None
    configuration: Optional[str] = None
    # quantidade do  ativo
    quantity: Optional[int] = None
    # unidade da quantidade
    unit: Optional[str] = None
    by_agile: bool = Field(
        serialization_alias="byAgile",
        default=False,
    )


class NewAssetSchema(BaseSchema):
    """New asset schema"""

    type_id: Optional[str] = Field(
        alias="typeId",
        serialization_alias="type_id",
        default=None,
    )
    clothing_size_id: Optional[str] = Field(
        alias="clothingSizeId",
        serialization_alias="clothing_size_id",
        default=None,
    )
    status_id: Optional[str] = Field(
        alias="statusId",
        serialization_alias="status_id",
        default=None,
    )

    code: Optional[str] = None
    # tombo - regiOptional[str]o patrimonial
    register_number: Optional[str] = Field(
        alias="registerNumber",
        serialization_alias="register_number",
        default=None,
    )
    description: Optional[str] = None
    # fornecedor
    supplier: Optional[str] = None
    # garantia
    assurance_date: Optional[date] = Field(
        alias="assuranceDate",
        serialization_alias="assurance_date",
        default=None,
    )
    observations: Optional[str] = None
    discard_reason: Optional[str] = Field(
        alias="discardReason",
        serialization_alias="discard_reason",
        default=None,
    )
    # padrão
    pattern: Optional[str] = None
    operational_system: Optional[str] = Field(
        alias="operationalSystem",
        serialization_alias="operational_system",
        default=None,
    )
    serial_number: Optional[str] = Field(
        alias="serialNumber",
        serialization_alias="serial_number",
        default=None,
    )
    imei: Optional[str] = None
    acquisition_date: Optional[date] = Field(
        alias="acquisitionDate",
        serialization_alias="acquisition_date",
        default=None,
    )
    value: float
    # pacote office
    ms_office: Optional[bool] = Field(
        alias="msOffice",
        serialization_alias="ms_office",
        default=None,
    )
    line_number: Optional[str] = Field(
        alias="lineNumber",
        serialization_alias="line_number",
        default=None,
    )
    # operadora
    operator: Optional[str] = None
    # modelo
    model: Optional[str] = None
    # acessórios
    accessories: Optional[str] = None
    configuration: Optional[str] = None
    # quantidade do  ativo
    quantity: Optional[int] = None
    # unidade da quantidade
    unit: Optional[str] = None


class UpdateAssetSchema(BaseSchema):
    """Update asset schema"""

    observations: Optional[str] = None


class InactivateAssetSchema(BaseSchema):
    """Inactivate asset schema"""

    active: bool
