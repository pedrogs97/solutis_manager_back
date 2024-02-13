"""Auth filters"""

from datetime import date
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.asset.models import (
    AssetClothingSizeModel,
    AssetModel,
    AssetStatusModel,
    AssetTypeModel,
)


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


class AssetTypeFilter(Filter):
    """Asset type filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetTypeModel


class AssetStatusFilter(Filter):
    """Asset status filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetStatusModel


class AssetClothingSizeFilter(Filter):
    """Asset clothing size filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetClothingSizeModel


class AssetFilter(Filter):
    """Asset filters"""

    code__ilike: Optional[str] = None
    description__ilike: Optional[str] = None
    register_number__ilike: Optional[str] = None
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
    asset_clothing_size: Optional[AssetClothingSizeFilter] = FilterDepends(
        with_prefix("asset_clothing_size", AssetClothingSizeFilter)
    )
    order_by: List[str] = ["code"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = AssetModel
        search_model_fields = ["code", "description", "register_number", "supplier"]
