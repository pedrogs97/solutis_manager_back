"""People filters"""

from datetime import date
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.datasync.models import (
    CostCenterTOTVSModel,
    EmployeeEducationalLevelTOTVSModel,
    EmployeeGenderTOTVSModel,
    EmployeeMaritalStatusTOTVSModel,
    EmployeeNationalityTOTVSModel,
    EmployeeRoleTOTVSModel,
)
from src.people.models import EmployeeModel


class CostCenterFilter(Filter):
    """Cost center filter"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = CostCenterTOTVSModel


class EmployeeMaritalStatusFilter(Filter):
    """Marital Status filter"""

    description: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeMaritalStatusTOTVSModel


class EmployeeGenderFilter(Filter):
    """Gender filter"""

    description: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeGenderTOTVSModel


class EmployeeNationalityFilter(Filter):
    """Nationality filter"""

    description: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeNationalityTOTVSModel


class EmployeeRoleFilter(Filter):
    """Role filter"""

    name: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeRoleTOTVSModel


class EmployeeEducationalLevelFilter(Filter):
    """Educational level filter"""

    description: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = EmployeeEducationalLevelTOTVSModel


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
    status__ilike: Optional[str] = None
    full_name__ilike: Optional[str] = None
    taxpayer_identification__ilike: Optional[str] = None
    national_identification__ilike: Optional[str] = None
    cell_phone__ilike: Optional[str] = None
    email__ilike: Optional[str] = None
    manager__ilike: Optional[str] = None
    registration__ilike: Optional[str] = None
    legal_person: Optional[bool] = None
    employer_number__ilike: Optional[str] = None
    employer_address__ilike: Optional[str] = None
    employer_name__ilike: Optional[str] = None
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
            "email",
        ]
