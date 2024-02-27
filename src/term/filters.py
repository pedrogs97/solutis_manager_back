"""Lending Filters"""

from datetime import date
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.lending.filters import WorkloadFilter
from src.people.filters import CostCenterFilter, EmployeeFullNameFilter
from src.term.models import TermModel, TermStatusModel


class TermStatusFilter(Filter):
    """Term status filters"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = TermStatusModel


class TermFilter(Filter):
    """Term filters"""

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
    workload: Optional[WorkloadFilter] = FilterDepends(
        with_prefix("workload", WorkloadFilter)
    )
    cost_center: Optional[CostCenterFilter] = FilterDepends(
        with_prefix("cost_center", CostCenterFilter)
    )
    status: Optional[TermStatusFilter] = FilterDepends(
        with_prefix("status", TermStatusFilter)
    )
    order_by: List[str] = ["number"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = TermModel
        search_model_fields = ["number", "manager", "glpi_number"]
