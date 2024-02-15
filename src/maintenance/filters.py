"""Maintenance filters"""

from datetime import date
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.asset.filters import AssetIdFilter
from src.maintenance.models import (
    MaintenanceActionModel,
    MaintenanceModel,
    MaintenanceStatusModel,
    UpgradeModel,
)


class MaintenanceStatusFilter(Filter):
    """Maintenance status filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = MaintenanceStatusModel


class MaintenanceActionFilter(Filter):
    """Maintenance acition filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = MaintenanceActionModel


class MaintenanceFilter(Filter):
    """Maintenance filters"""

    glpi_number__ilike: Optional[str] = None
    glpi_number__like: Optional[str] = None
    supplier_service_order__like: Optional[str] = None
    supplier_service_order__ilike: Optional[str] = None
    supplier_number__like: Optional[str] = None
    supplier_number__ilike: Optional[str] = None
    open_date__lte: Optional[date] = None
    open_date__gte: Optional[date] = None
    close_date__lte: Optional[date] = None
    close_date__gte: Optional[date] = None
    maintenance_action: Optional[MaintenanceActionFilter] = FilterDepends(
        with_prefix("maintenance_action", MaintenanceActionFilter)
    )
    maintenance_status: Optional[MaintenanceStatusFilter] = FilterDepends(
        with_prefix("maintenance_status", MaintenanceStatusFilter)
    )
    asset: Optional[AssetIdFilter] = FilterDepends(with_prefix("asset", AssetIdFilter))
    order_by: List[str] = ["glpi_number"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = MaintenanceModel
        search_model_fields = [
            "glpi_number",
            "supplier_number",
            "supplier_service_order",
        ]


class UpgradeFilter(Filter):
    """Upgrade filters"""

    glpi_number__ilike: Optional[str] = None
    supplier__ilike: Optional[str] = None
    open_date__lte: Optional[date] = None
    open_date__gte: Optional[date] = None
    close_date__lte: Optional[date] = None
    close_date__gte: Optional[date] = None
    maintenance_status: Optional[MaintenanceStatusFilter] = FilterDepends(
        with_prefix("maintenance_status", MaintenanceStatusFilter)
    )
    asset: Optional[AssetIdFilter] = FilterDepends(with_prefix("asset", AssetIdFilter))
    order_by: List[str] = ["glpi_number"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = UpgradeModel
        search_model_fields = ["glpi_number", "supplier"]
