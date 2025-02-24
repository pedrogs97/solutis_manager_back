"""Asset schemas"""

from datetime import date, datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from pydantic import Field, field_validator

from src.asset.enums import DisposalReasonEnum
from src.asset.models import AssetModel
from src.backends import get_db_session
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

    * NOTEBOOK
    * DESKTOP
    * MONITOR
    * WEBCAM
    * TELEFONIA
    * VESTIMENTA
    * FERRAMENTAS
    * IMPRESSORA
    * TABLET
    * HEADSET
    * MOUSE/TECLADO
    * HD EXTERNO
    * PENDRIVE
    """

    id: int
    code: str
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
    asset_type: Optional[str] = Field(
        serialization_alias="assetType",
        default=None,
    )
    value: Optional[float] = None


class DisposalAssetReasonSerializerSchema(BaseSchema):
    """Disposal asset reason serializer schema"""

    id: int
    name: DisposalReasonEnum


class DisposalAssetSerializerSchema(BaseSchema):
    """Disposal asset serializer schema"""

    reason: DisposalAssetReasonSerializerSchema
    justification: Optional[str] = None
    observations: Optional[str] = None
    disposal_date: date = Field(serialization_alias="disposalDate")


class AssetSerializerSchema(BaseSchema):
    """Asset serializer schema"""

    id: int
    type: Optional[AssetTypeSerializerSchema] = None
    status: Optional[AssetStatusSerializerSchema] = None

    invoice_number: Optional[str] = Field(
        serialization_alias="invoiceNumber",
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
    value: Optional[float] = 0.0
    depreciation: Optional[float] = None
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
    maintenance_status: str = Field(serialization_alias="maintenanceStatus")
    upgrade_status: str = Field(serialization_alias="upgradeStatus")
    alert: Optional[str] = ""
    disposal: Optional[DisposalAssetSerializerSchema] = None


class NewAssetSchema(BaseSchema):
    """New asset schema"""

    type_id: Optional[str] = Field(
        alias="typeId",
        serialization_alias="type_id",
        default=None,
    )
    status_id: Optional[str] = Field(
        alias="statusId",
        serialization_alias="status_id",
        default=None,
    )

    code: Optional[str] = None
    # tombo - regitro patrimonial
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

    @field_validator("imei")
    @classmethod
    def validate_imei(cls, value: str) -> str:
        """Validate imei"""
        db_session = get_db_session()
        if db_session.query(
            db_session.query(AssetModel).filter(AssetModel.imei == value).exists()
        ).scalar():
            db_session.close()
            raise HTTPException(
                status_code=400, detail={"field": "imei", "error": "IMEI já existe"}
            )
        db_session.close()
        return value

    @field_validator("register_number")
    @classmethod
    def validate_register_number(cls, value: str) -> str:
        """Validate register number"""
        db_session = get_db_session()
        if db_session.query(
            db_session.query(AssetModel)
            .filter(AssetModel.register_number == value)
            .exists()
        ).scalar():
            db_session.close()
            raise HTTPException(
                status_code=400,
                detail={"field": "register_number", "error": "Patrimônio já existe"},
            )
        db_session.close()
        return value


class UpdateAssetSchema(BaseSchema):
    """Update asset schema"""

    type_id: Optional[int] = Field(alias="typeId", default=None)
    status_id: Optional[int] = Field(alias="statusId", default=None)
    code: Optional[str] = None
    # tombo - regitro patrimonial
    register_number: Optional[str] = Field(
        alias="registerNumber",
        default=None,
    )
    description: Optional[str] = None
    # fornecedor
    supplier: Optional[str] = None
    # garantia
    assurance_date: Optional[date] = Field(
        alias="assuranceDate",
        default=None,
    )
    observations: Optional[str] = None
    # padrão
    pattern: Optional[str] = None
    operational_system: Optional[str] = Field(
        alias="operationalSystem",
        default=None,
    )
    serial_number: Optional[str] = Field(
        alias="serialNumber",
        default=None,
    )
    imei: Optional[str] = None
    acquisition_date: Optional[date] = Field(
        alias="acquisitionDate",
        default=None,
    )
    value: Optional[float] = None
    # pacote office
    ms_office: Optional[bool] = Field(
        alias="msOffice",
        default=None,
    )
    line_number: Optional[str] = Field(
        alias="lineNumber",
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


class InactivateAssetSchema(BaseSchema):
    """Inactivate asset schema"""

    active: bool


class DisposalAssetSchema(BaseSchema):
    """Disposal asset schema"""

    reason: DisposalAssetReasonSerializerSchema
    justification: Optional[str] = None
    observations: Optional[str] = None
    disposal_date: date = Field(alias="disposalDate")
