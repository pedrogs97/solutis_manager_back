"""Auth filters"""

from datetime import date
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.asset.models import AssetModel, AssetStatusModel, AssetTypeModel


class AssetShortFilter(Filter):
    """Asset short filters"""

    code__ilike: Optional[str] = None
    code__like: Optional[str] = None
    description__like: Optional[str] = None
    description__ilike: Optional[str] = None
    register_number__like: Optional[str] = None
    register_number__ilike: Optional[str] = None
    order_by: List[str] = ["code"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetModel
        search_model_fields = ["code"]


class AssetIdFilter(Filter):
    """Asset id filters"""

    id: Optional[int] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetModel


class AssetTypeFilter(Filter):
    """Asset type filters"""

    name: Optional[str] = None
    id__in: Optional[List[int]] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetTypeModel


class AssetStatusFilter(Filter):
    """Asset status filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetStatusModel


class AssetFilter(Filter):
    """Asset filters"""

    code__ilike: Optional[str] = None
    description__ilike: Optional[str] = None
    register_number__ilike: Optional[str] = None
    serial_number__ilike: Optional[str] = None
    supplier__ilike: Optional[str] = None
    acquisition_date__gte: Optional[date] = None
    acquisition_date__lte: Optional[date] = None
    active: Optional[bool] = True
    by_agile: Optional[bool] = None
    asset_type: Optional[AssetTypeFilter] = FilterDepends(
        with_prefix("asset_type", AssetTypeFilter)
    )
    asset_status: Optional[AssetStatusFilter] = FilterDepends(
        with_prefix("asset_status", AssetStatusFilter)
    )
    order_by: List[str] = ["code"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetModel
        search_model_fields = ["code", "description", "register_number", "supplier"]


class AssetSelectFilter(Filter):
    """Asset select filters"""

    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetModel
        search_model_fields = ["description", "register_number"]
