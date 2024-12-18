""" Invetory router """

from typing import List, Optional, Union

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, Response
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
from src.inventory.backends import generate_token, verify_token
from src.inventory.schemas import AnswerInventorySerializer, EmployeeInventorySerializer
from src.inventory.service import InventoryService

inventory_router = APIRouter(prefix="/inventory", tags=["Inventory"])


@inventory_router.post("/get-employee/")
def get_employee_route(
    data: EmployeeInventorySerializer,
    db_session: Session = Depends(get_db_session),
):
    """Get employee route"""
    service = InventoryService(db_session)
    (inventory_by_employee, token_data) = service.get_employee(data)
    content = {"token": generate_token(token_data), "employee": inventory_by_employee}
    db_session.close()
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


@inventory_router.post("/answer/")
def post_answer_route(
    data: AnswerInventorySerializer,
    db_session: Session = Depends(get_db_session),
    token: dict = Depends(verify_token),
):
    """Post answer route"""
    service = InventoryService(db_session)
    service.create_invetory_answer(data, token.get("employee_id"))
    db_session.close()
    return Response(status_code=status.HTTP_201_CREATED)


@inventory_router.get("/get-employee-answer/")
def get_employee_answer_route(
    employee_ids: Optional[List[int]] = Query(
        description="Employee ids",
        alias="employeeIds",
        serialization_alias="employee_ids",
        default=None,
    ),
    year: Optional[int] = Query(ge=2023, description="Year", default=None),
    answered: Optional[bool] = Query(description="Answered", default=None),
    has_extra: Optional[bool] = Query(
        description="Has extra",
        default=None,
        alias="hasExtra",
        serialization_alias="has_extra",
    ),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "inventory", "model": "inventory", "action": "view"}
        )
    ),
):
    """Get employee answer route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    service = InventoryService(db_session)
    filters = {
        "employee_ids": employee_ids,
        "year": year,
        "answered": answered,
        "has_extra": has_extra,
    }
    inventory_by_employee = service.get_answers(filters, page, size)
    db_session.close()
    return inventory_by_employee
