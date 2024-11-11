""" Invetory router """

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.backends import get_db_session
from src.inventory.schemas import EmployeeInventorySerializer
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
