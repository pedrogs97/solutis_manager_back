"""People routes"""
from typing import List
from fastapi import APIRouter, status, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.backends import (
    get_db_session,
    PermissionChecker,
)
from app.people.schemas import (
    EmployeeTotvsSchema,
    NewEmployeeSchema,
    UpdateEmployeeSchema,
)
from app.people.service import EmployeeService
from app.config import (
    PAGINATION_NUMBER,
    MAX_PAGINATION_NUMBER,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    NOT_ALLOWED,
)

people_router = APIRouter(prefix="/people", tags=["People"])

employee_service = EmployeeService()


@people_router.post("/employee/update/")
async def post_updates_route(
    data: List[EmployeeTotvsSchema],
    db_session: Session = Depends(get_db_session),
):
    """Update employee from TOTVSroute"""
    employee_service.update_employees(data, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@people_router.post("/employees/")
async def post_create_employee_route(
    data: NewEmployeeSchema,
    db_session: Session = Depends(get_db_session),
    authenticated: bool = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "add"})
    ),
):
    """Creates employee route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = employee_service.create_employee(data, db_session)
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@people_router.patch("/employee/{employee_id}/")
async def patch_update_employee_route(
    employee_id: int,
    data: UpdateEmployeeSchema,
    db_session: Session = Depends(get_db_session),
    authenticated: bool = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "add"})
    ),
):
    """Update employee route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = employee_service.update_employee(employee_id, data, db_session)
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@people_router.put("/employee/{employee_id}/")
async def put_update_employee_route():
    """Update employee not implemented"""
    return JSONResponse(
        content="Not Implemented", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@people_router.get("/employees/")
async def get_list_employees_route(
    search: str = "",
    filter: str = None,
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated: bool = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "add"})
    ),
):
    """List employees and apply filters route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    return JSONResponse(
        content=employee_service.get_employees(db_session, search, filter, page, size),
        status_code=status.HTTP_200_OK,
    )


@people_router.get("/employees/{employee_id}/")
async def get_emplooyee_route(
    employee_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated: bool = Depends(
        PermissionChecker({"module": "people", "model": "employee", "action": "add"})
    ),
):
    """Get an employee route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    employee_service.get_employee(employee_id, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)
