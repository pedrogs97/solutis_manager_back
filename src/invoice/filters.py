"""Invoice filters"""

from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.asset.filters import AssetShortFilter
from src.invoice.models import InvoiceModel


class InvoiceFilter(Filter):
    """Invoice filters"""

    number__ilike: Optional[str] = None
    number__like: Optional[str] = None
    asset: Optional[AssetShortFilter] = FilterDepends(
        with_prefix("asset", AssetShortFilter)
    )
    order_by: List[str] = ["number"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = InvoiceModel
        search_model_fields = ["number"]
