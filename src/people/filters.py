"""People filters"""
from datetime import date
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.people.models import (
    CostCenterModel,
    EmployeeGenderModel,
    EmployeeMaritalStatusModel,
    EmployeeModel,
    EmployeeNationalityModel,
    EmployeeRoleModel,
)


class CostCenterFilter(Filter):
    """Cost center filter"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = CostCenterModel


class EmployeeMaritalStatusFilter(Filter):
    """Cost center filter"""

    description: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeMaritalStatusModel


class EmployeeGenderFilter(Filter):
    """Cost center filter"""

    description: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeGenderModel


class EmployeeNationalityFilter(Filter):
    """Cost center filter"""

    description: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeNationalityModel


class EmployeeRoleFilter(Filter):
    """Cost center filter"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeRoleModel


class EmployeeFullNameFilter(Filter):
    """Employee name filter"""

    full_name__ilike: Optional[str] = None
    full_name__like: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeModel


class EmployeeFilter(Filter):
    """Employee filters"""

    code__ilike: Optional[str] = None
    code__like: Optional[str] = None
    status: Optional[str] = None
    status__ilike: Optional[str] = None
    status__like: Optional[str] = None
    full_name__ilike: Optional[str] = None
    full_name__like: Optional[str] = None
    taxpayer_identification__ilike: Optional[str] = None
    taxpayer_identification__like: Optional[str] = None
    national_identification__ilike: Optional[str] = None
    national_identification__like: Optional[str] = None
    cell_phone__ilike: Optional[str] = None
    cell_phone__like: Optional[str] = None
    email__ilike: Optional[str] = None
    email__like: Optional[str] = None
    manager__ilike: Optional[str] = None
    manager__like: Optional[str] = None
    registration__ilike: Optional[str] = None
    registration__like: Optional[str] = None
    legal_person: Optional[bool] = None
    employer_number__ilike: Optional[str] = None
    employer_number__like: Optional[str] = None
    employer_address__ilike: Optional[str] = None
    employer_address__like: Optional[str] = None
    employer_name__ilike: Optional[str] = None
    employer_name__like: Optional[str] = None
    birthday__gte: Optional[date] = None
    birthday__lte: Optional[date] = None
    admission_date__gte: Optional[date] = None
    admission_date__lte: Optional[date] = None
    role: Optional[EmployeeRoleFilter] = FilterDepends(
        with_prefix("role", EmployeeRoleFilter)
    )
    nationality: Optional[EmployeeNationalityFilter] = FilterDepends(
        with_prefix("nationality", EmployeeNationalityFilter)
    )
    marital_status: Optional[EmployeeMaritalStatusFilter] = FilterDepends(
        with_prefix("marital_status", EmployeeMaritalStatusFilter)
    )
    gender: Optional[EmployeeGenderFilter] = FilterDepends(
        with_prefix("gender", EmployeeGenderFilter)
    )
    order_by: List[str] = []
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeModel
        search_model_fields = [
            "code",
            "full_name",
            "taxpayer_identification",
            "registration",
        ]
