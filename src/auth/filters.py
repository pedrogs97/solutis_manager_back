"""Auth filters"""
from datetime import date
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.auth.models import GroupModel, PermissionModel, UserModel
from src.people.filters import EmployeeFullNameFilter


class PermissionFilter(Filter):
    """Permission filters"""

    module__ilike: Optional[str] = None
    module__like: Optional[str] = None
    model__ilike: Optional[str] = None
    model__like: Optional[str] = None
    action__ilike: Optional[str] = None
    action__like: Optional[str] = None
    description__ilike: Optional[str] = None
    description__like: Optional[str] = None
    order_by: List[str] = []
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = PermissionModel
        search_model_fields = ["module", "model", "description"]


class GroupFilter(Filter):
    """Group filters"""

    name: Optional[str] = None
    name__ilike: Optional[str] = None
    name__like: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = GroupModel
        search_model_fields = ["name"]


class UserFilter(Filter):
    """User filters"""

    employee: Optional[EmployeeFullNameFilter] = FilterDepends(
        with_prefix("employee", EmployeeFullNameFilter)
    )
    group: Optional[GroupFilter] = FilterDepends(with_prefix("group", GroupFilter))
    username__ilike: Optional[str] = None
    username__like: Optional[str] = None
    email__ilike: Optional[str] = None
    email__like: Optional[str] = None
    is_staff: Optional[bool] = None
    is_active: Optional[bool] = None
    last_login_in__gte: Optional[date] = None
    last_login_in__lte: Optional[date] = None
    order_by: List[str] = []
    search: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = UserModel
        search_model_fields = ["username", "email", "group", "employee"]
