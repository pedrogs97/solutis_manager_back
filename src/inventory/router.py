""" Invetory router """

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.backends import get_db_session
from src.inventory.backends import verify_token
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
    inventory_by_employee = service.get_employee(data)
    db_session.close()
    return JSONResponse(content=inventory_by_employee, status_code=status.HTTP_200_OK)


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
    return JSONResponse(status_code=status.HTTP_201_CREATED)
