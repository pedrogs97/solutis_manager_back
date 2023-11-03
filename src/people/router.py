"""People routes"""
from typing import List, Union

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.backends import PermissionChecker, get_db_session
from src.config import (MAX_PAGINATION_NUMBER, NOT_ALLOWED,
                        PAGE_NUMBER_DESCRIPTION, PAGE_SIZE_DESCRIPTION,
                        PAGINATION_NUMBER)
from src.people.schemas import (EmployeeGenderTotvsSchema,
                                EmployeeMatrimonialStatusTotvsSchema,
                                EmployeeNationalityTotvsSchema,
                                EmployeeRoleTotvsSchema, EmployeeTotvsSchema,
                                NewEmployeeSchema, UpdateEmployeeSchema)
from src.people.service import EmployeeService

people_router = APIRouter(prefix="/people", tags=["People"])

employee_service = EmployeeService()


@people_router.post("/employee/update/")
async def post_updates_route(
    data: List[EmployeeTotvsSchema],
    db_session: Session = Depends(get_db_session),
):
    """Update employee from TOTVSroute"""
    employee_service.update_employee_totvs(data, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@people_router.post("/employee/matrimonial-status/update/")
async def post_matrimonial_status_updates_route(
    data: List[EmployeeMatrimonialStatusTotvsSchema],
    db_session: Session = Depends(get_db_session),
):
    """Update employee from TOTVSroute"""
    employee_service.update_matrimonial_status_totvs(data, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@people_router.post("/employee/gender/update/")
async def post_gender_updates_route(
    data: List[EmployeeGenderTotvsSchema],
    db_session: Session = Depends(get_db_session),
):
    """Update employee from TOTVSroute"""
    employee_service.update_gender_totvs(data, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@people_router.post("/employee/nationality/update/")
async def post_nationality_updates_route(
    data: List[EmployeeNationalityTotvsSchema],
    db_session: Session = Depends(get_db_session),
):
    """Update employee from TOTVSroute"""
    employee_service.update_nationality_totvs(data, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@people_router.post("/employee/role/update/")
async def post_role_updates_route(
    data: List[EmployeeRoleTotvsSchema],
    db_session: Session = Depends(get_db_session),
):
    """Update employee from TOTVSroute"""
    employee_service.update_role_totvs(data, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@people_router.post("/employees/")
async def post_create_employee_route(
    data: NewEmployeeSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "add"})
    ),
):
    """Creates employee route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = employee_service.create_employee(data, db_session, authenticated_user)
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@people_router.patch("/employee/{employee_id}/")
async def patch_update_employee_route(
    employee_id: int,
    data: UpdateEmployeeSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "edit"})
    ),
):
    """Update employee route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = employee_service.update_employee(
        employee_id, data, db_session, authenticated_user
    )
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@people_router.put("/employee/{employee_id}/")
async def put_update_employee_route():
    """Update employee Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@people_router.get("/employees/")
async def get_list_employees_route(
    search: str = "",
    filter_list: str = None,
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "view"})
    ),
):
    """List employees and apply filters route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    return JSONResponse(
        content=employee_service.get_employees(
            db_session, search, filter_list, page, size
        ),
        status_code=status.HTTP_200_OK,
    )


@people_router.get("/employees/{employee_id}/")
async def get_emplooyee_route(
    employee_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "view"})
    ),
):
    """Get an employee route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    employee_service.get_employee(employee_id, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@people_router.get("/employees/history/lending/{employee_id}/")
async def get_emplooyee_lending_history_route(
    employee_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "view"})
    ),
):
    """Get an employee route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer_list = employee_service.get_employee_lending_history(
        employee_id, db_session
    )
    return JSONResponse(
        content=[
            serializer.model_copy(by_alias=True) for serializer in serializer_list
        ],
        status_code=status.HTTP_200_OK,
    )
