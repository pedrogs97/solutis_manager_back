"""People routes"""

from typing import Union

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from fastapi_filter import FilterDepends
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.backends import PermissionChecker, get_db_session
from src.config import (
    MAX_PAGINATION_NUMBER,
    NOT_ALLOWED,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    PAGINATION_NUMBER,
)
from src.people.filters import (
    CostCenterFilter,
    EmployeeFilter,
    EmployeeGenderFilter,
    EmployeeMaritalStatusFilter,
    EmployeeNationalityFilter,
    EmployeeRoleFilter,
    EmployeeSelectFilter,
)
from src.people.schemas import NewEmployeeSchema, UpdateEmployeeSchema
from src.people.service import EmpleoyeeGeneralSerivce, EmployeeService

people_router = APIRouter(prefix="/people", tags=["People"])

employee_service = EmployeeService()
general_service = EmpleoyeeGeneralSerivce()


@people_router.post("/employees/")
def post_create_employee_route(
    data: NewEmployeeSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "add"})
    ),
):
    """Creates employee route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = employee_service.create_employee(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@people_router.patch("/employees/{employee_id}/")
def patch_update_employee_route(
    employee_id: int,
    data: UpdateEmployeeSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "edit"})
    ),
):
    """Update employee route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = employee_service.update_employee(
        employee_id, data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@people_router.put("/employees/{employee_id}/")
def put_update_employee_route():
    """Update employee Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@people_router.get("/employees/")
def get_list_employees_route(
    employee_filters: EmployeeFilter = FilterDepends(EmployeeFilter),
    ids: str = Query(""),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "view"})
    ),
):
    """List employees and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    employees = employee_service.get_employees(
        db_session, employee_filters, ids, fields, page, size
    )
    db_session.close()
    return employees


@people_router.get("/employees-select/")
def get_select_employees_route(
    employee_filters: EmployeeSelectFilter = FilterDepends(EmployeeSelectFilter),
    ids: str = Query(""),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            [
                {"module": "auth", "model": "user", "action": "add"},
                {"module": "auth", "model": "user", "action": "edit"},
                {"module": "lending", "model": "lending", "action": "add"},
                {"module": "lending", "model": "lending", "action": "edit"},
                {"module": "lending", "model": "term", "action": "add"},
                {"module": "lending", "model": "term", "action": "edit"},
                {"module": "asset", "model": "maintenance", "action": "add"},
                {"module": "asset", "model": "maintenance", "action": "edit"},
                {"module": "asset", "model": "asset", "action": "add"},
                {"module": "asset", "model": "asset", "action": "edit"},
            ]
        )
    ),
):
    """List for select employees route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    employees = employee_service.get_employees(
        db_session, employee_filters, ids, "id,full_name", 1, size
    )
    db_session.close()
    return employees


@people_router.get("/employees/{employee_id}/")
def get_emplooyee_route(
    employee_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "view"})
    ),
):
    """Get an employee route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = employee_service.get_employee(employee_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@people_router.get("/employees/history/lending/{employee_id}/")
def get_emplooyee_lending_history_route(
    employee_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "view"})
    ),
):
    """Get an employee route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer_list = employee_service.get_employee_lending_history(
        employee_id, db_session
    )
    db_session.close()
    return JSONResponse(
        content=serializer_list,
        status_code=status.HTTP_200_OK,
    )


@people_router.get("/employees/history/term/{employee_id}/")
def get_emplooyee_term_history_route(
    employee_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "view"})
    ),
):
    """Get an employee route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer_list = employee_service.get_employee_term_history(
        employee_id, db_session
    )
    db_session.close()
    return JSONResponse(
        content=serializer_list,
        status_code=status.HTTP_200_OK,
    )


@people_router.get("/nationalities/")
def get_list_nationalities_route(
    nationality_filters: EmployeeNationalityFilter = FilterDepends(
        EmployeeNationalityFilter
    ),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "people", "model": "nationality", "action": "view"}
        )
    ),
):
    """List nationalities and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    nationalities = general_service.get_nationalities(
        db_session, nationality_filters, fields
    )
    db_session.close()
    return JSONResponse(content=nationalities, status_code=status.HTTP_200_OK)


@people_router.get("/marital-status/")
def get_list_marital_status_route(
    marital_status_filters: EmployeeMaritalStatusFilter = FilterDepends(
        EmployeeMaritalStatusFilter
    ),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "people", "model": "marital_status", "action": "view"}
        )
    ),
):
    """List marital status and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    marital_status = general_service.get_marital_status(
        db_session, marital_status_filters, fields
    )
    db_session.close()
    return JSONResponse(content=marital_status, status_code=status.HTTP_200_OK)


@people_router.get("/center-cost/")
def get_list_center_cost_route(
    cost_center_filters: CostCenterFilter = FilterDepends(CostCenterFilter),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "people", "model": "center_cost", "action": "view"}
        )
    ),
):
    """List center cost and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    center_cost = general_service.get_center_cost(
        db_session, cost_center_filters, fields
    )
    db_session.close()
    return JSONResponse(content=center_cost, status_code=status.HTTP_200_OK)


@people_router.get("/genders/")
def get_list_genders_route(
    gender_filters: EmployeeGenderFilter = FilterDepends(EmployeeGenderFilter),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "gender", "action": "view"})
    ),
):
    """List genders and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    genders = general_service.get_genders(db_session, gender_filters, fields)
    db_session.close()
    return JSONResponse(content=genders, status_code=status.HTTP_200_OK)


@people_router.get("/roles/")
def get_list_roles_route(
    role_filters: EmployeeRoleFilter = FilterDepends(EmployeeRoleFilter),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "role", "action": "view"})
    ),
):
    """List roles and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    roles = general_service.get_roles(db_session, role_filters, fields)
    db_session.close()
    return JSONResponse(content=roles, status_code=status.HTTP_200_OK)


@people_router.get("/educational-level/")
def get_list_educational_levels_route(
    educational_level_filters: EmployeeRoleFilter = FilterDepends(EmployeeRoleFilter),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "view"})
    ),
):
    """List educational levels and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    educational_levels = general_service.get_educational_levels(
        db_session, educational_level_filters, fields
    )
    db_session.close()
    return JSONResponse(content=educational_levels, status_code=status.HTTP_200_OK)
