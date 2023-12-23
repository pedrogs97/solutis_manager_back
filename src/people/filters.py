"""People filters"""
from datetime import date
from typing import List, Optional

from fastapi_filter.contrib.sqlalchemy import Filter

from src.people.models import EmployeeModel


class EmployeeFullNameFilter(Filter):
    """Employee name fitler"""

    full_name: Optional[str] = None
    full_name__ilike: Optional[str] = None
    full_name__like: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeModel


class EmployeeFilter(Filter):
    """Employee filters"""

    code: Optional[str] = None
    code__ilike: Optional[str] = None
    code__like: Optional[str] = None
    status: Optional[str] = None
    status__ilike: Optional[str] = None
    status__like: Optional[str] = None
    full_name: Optional[str] = None
    full_name__ilike: Optional[str] = None
    full_name__like: Optional[str] = None
    is_staff: Optional[bool] = None
    is_active: Optional[bool] = None
    last_login_in__gte: Optional[date] = None
    last_login_in__lte: Optional[str] = None
    order_by: List[str] = []
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeModel
        search_model_fields = ["code", "status", "city"]
