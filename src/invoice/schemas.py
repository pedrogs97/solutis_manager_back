"""Invoice schemas"""

from typing import Optional

from pydantic import Field

from src.asset.schemas import AssetShortSerializerSchema
from src.schemas import BaseSchema


class InvoiceSerializerSchema(BaseSchema):
    """Invoice serializer schema"""

    id: int
    number: str
    path: Optional[str] = None
    file_name: Optional[str] = None
    deleted_at: Optional[str] = Field(serialization_alias="deletedAt", default=None)
    asset: AssetShortSerializerSchema


class NewInvoiceSchema(BaseSchema):
    """New invoice schema"""

    number: str
    asset_id: int = Field(alias="assetId")
