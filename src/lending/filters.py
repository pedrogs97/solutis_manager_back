"""Lending Filters"""
from datetime import date
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.asset.filters import AssetShortFilter
from src.lending.models import (
    DocumentModel,
    DocumentTypeModel,
    LendingModel,
    WitnessModel,
    WorkloadModel,
)
from src.people.filters import CostCenterFilter, EmployeeFullNameFilter


class DocumentTypeFilter(Filter):
    """Document type filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = DocumentTypeModel


class DocumentFilter(Filter):
    """Document filters"""

    doc_type: Optional[DocumentTypeFilter] = FilterDepends(
        with_prefix("doc_type", DocumentTypeFilter)
    )

    class Constants(Filter.Constants):
        """Filter constants"""

        model = DocumentModel


class WorkloadFilter(Filter):
    """Workload filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = WorkloadModel


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
    employee: Optional[EmployeeFullNameFilter] = FilterDepends(
        with_prefix("employee", EmployeeFullNameFilter)
    )
    asset: Optional[AssetShortFilter] = FilterDepends(
        with_prefix("asset", AssetShortFilter)
    )
    workload: Optional[WorkloadFilter] = FilterDepends(
        with_prefix("workload", WorkloadFilter)
    )
    cost_center: Optional[CostCenterFilter] = FilterDepends(
        with_prefix("cost_center", CostCenterFilter)
    )
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
