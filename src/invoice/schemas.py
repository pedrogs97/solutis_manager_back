"""Invoice schemas"""

from typing import List, Optional

from pydantic import Field, field_serializer

from src.asset.schemas import AssetShortSerializerSchema
from src.schemas import BaseSchema


class InvoiceSerializerSchema(BaseSchema):
    """Invoice serializer schema"""

    id: int
    number: str
    path: Optional[str] = None
    file_name: Optional[str] = None
    deleted_at: Optional[str] = Field(serialization_alias="deletedAt", default=None)
    assets: List[AssetShortSerializerSchema]
    total_value: float = Field(serialization_alias="totalValue", default=0.0)
    total_assets: int = Field(serialization_alias="totalAssets", default=0)

    @field_serializer("total_value", check_fields=False)
    def calculate_total_value(self, value, info) -> float:
        """Total value of invoice"""
        return round(sum(asset.value for asset in self.assets), 2)

    @field_serializer("total_assets", check_fields=False)
    def calculate_total_assets(self, value, info) -> int:
        """Total assets of invoice"""
        return len(self.assets)


class NewInvoiceSchema(BaseSchema):
    """New invoice schema"""

    number: str
    assets_id: List[int] = Field(alias="assetsId")
