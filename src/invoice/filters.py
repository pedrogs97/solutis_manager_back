"""Invoice filters"""
from decimal import Decimal
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.asset.filters import AssetShortFilter
from src.invoice.models import InvoiceModel


class InvoiceFilter(Filter):
    """Invoice filters"""

    number__ilike: Optional[str] = None
    number__like: Optional[str] = None
    description: Optional[str] = None
    description__like: Optional[str] = None
    description__ilike: Optional[str] = None
    toal_value__lte: Optional[Decimal] = None
    toal_value__gte: Optional[Decimal] = None
    total_quantity__lte: Optional[Decimal] = None
    total_quantity__gte: Optional[Decimal] = None
    asset: Optional[AssetShortFilter] = FilterDepends(
        with_prefix("asset", AssetShortFilter)
    )
    order_by: List[str] = ["number"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = InvoiceModel
        search_model_fields = ["number"]
