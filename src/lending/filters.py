"""Lending Filters"""

from datetime import date
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.asset.filters import AssetShortFilter, AssetTypeFilter
from src.lending.models import (
    LendingModel,
    LendingStatusModel,
    WitnessModel,
    WorkloadModel,
)
from src.lending.schemas import LendingBUEnum
from src.people.filters import CostCenterFilter, EmployeeFullNameFilter


class WorkloadFilter(Filter):
    """Workload filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = WorkloadModel


class LendingStatusFilter(Filter):
    """Lending status filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = LendingStatusModel


class LendingFilter(Filter):
    """Lending filters"""

    number__ilike: Optional[str] = None
    number__like: Optional[str] = None
    manager__like: Optional[str] = None
    manager__ilike: Optional[str] = None
    glpi_number__like: Optional[str] = None
    glpi_number__ilike: Optional[str] = None
    signed_date__gte: Optional[date] = None
    signed_date__lte: Optional[date] = None
    created_at__gte: Optional[date] = None
    created_at__lte: Optional[date] = None
    employee: Optional[EmployeeFullNameFilter] = FilterDepends(
        with_prefix("employee", EmployeeFullNameFilter)
    )
    asset: Optional[AssetShortFilter] = FilterDepends(
        with_prefix("asset", AssetShortFilter)
    )
    asset_type: Optional[AssetTypeFilter] = FilterDepends(
        with_prefix("asset_type", AssetTypeFilter)
    )
    workload: Optional[WorkloadFilter] = FilterDepends(
        with_prefix("workload", WorkloadFilter)
    )
    cost_center: Optional[CostCenterFilter] = FilterDepends(
        with_prefix("cost_center", CostCenterFilter)
    )
    status: Optional[LendingStatusFilter] = FilterDepends(
        with_prefix("status", LendingStatusFilter)
    )
    bu: Optional[LendingBUEnum] = None
    order_by: List[str] = ["number"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = LendingModel
        search_model_fields = ["number", "manager", "glpi_number"]


class WitnessFilter(Filter):
    """Witness filters"""

    employee: Optional[EmployeeFullNameFilter] = FilterDepends(
        with_prefix("employee", EmployeeFullNameFilter)
    )

    class Constants(Filter.Constants):
        """Filter constants"""

        model = WitnessModel
