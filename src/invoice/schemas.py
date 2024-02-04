"""Invoice schemas"""

from typing import List, Optional

from pydantic import Field

from src.schemas import BaseSchema


class AssetInvoiceSerializerSchema(BaseSchema):
    """Asset infos for invoice serializer schema"""

    asset_id: int
    quantity: int
    unit_value: float


class InvoiceSerializerSchema(BaseSchema):
    """Invoice serializer schema"""

    id: int
    number: str
    path: Optional[str] = None
    file_name: Optional[str] = None
    total_value: float = Field(serialization_alias="totalValue")
    total_quantity: float = Field(serialization_alias="totalQuantity")
    assets_invoice: List[AssetInvoiceSerializerSchema] = Field(
        serialization_alias="assetsInvoice", default=[]
    )


class NewAssetInvoice(BaseSchema):
    """Asset infos for invoice schema"""

    asset_id: int
    quantity: int
    unit_value: float = Field(serialization_alias="unitValue")


class NewInvoiceSchema(BaseSchema):
    """New invoice schema"""

    number: str
    total_value: float = Field(alias="totalValue")
    total_quantity: int = Field(alias="totalQuantity")
    assets: List[NewAssetInvoice]


class UploadInvoiceSchema(BaseSchema):
    """Schema for upload invoice"""

    invoice_id: int = Field(alias="invoiceId")
