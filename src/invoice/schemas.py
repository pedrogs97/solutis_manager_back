"""Invoice schemas"""
from typing import List

from pydantic import Field

from src.lending.schemas import AssetSerializerSchema
from src.schemas import BaseSchema


class InvoiceSerializerSchema(BaseSchema):
    """Invoice serializer schema"""

    id: int
    number: str
    path: str
    file_name: str
    total_value: float = Field(serialization_alias="totalValue")
    total_quantity: float = Field(serialization_alias="totalQuantity")
    assets: List[AssetSerializerSchema] = []


class NewInvoiceSchema(BaseSchema):
    """New invoice schema"""

    number: str
    total_value: float = Field(alias="totalValue")
    total_quantity: float = Field(alias="totalQuantity")
    assets: List[int]


class UploadInvoiceSchema(BaseSchema):
    """Schema for upload invoice"""

    invoice_id: int = Field(alias="invoiceId")
