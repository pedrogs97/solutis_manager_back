"""Inventory service"""

from fastapi import HTTPException
from sqlalchemy.orm import Session, with_loader_criteria

from src.inventory.schemas import EmployeeInventorySerializer
from src.lending.models import LendingModel
from src.people.models import EmployeeModel
from src.term.models import TermModel


class InventoryService:
    """Inventory service"""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_employee(self, data: EmployeeInventorySerializer) -> dict:
        """Get employee"""
        employee = (
            self.db_session.query(EmployeeModel)
            .options(
                with_loader_criteria(
                    LendingModel,
                    LendingModel.deleted == False,
                    include_aliases=True,
                )
            )
            .options(
                with_loader_criteria(
                    TermModel,
                    TermModel.deleted == False,
                    include_aliases=True,
                )
            )
            .filter(
                EmployeeModel.registration == data.registration,
                EmployeeModel.birthday == data.birthday,
            )
            .first()
        )
        if not employee:
            self.db_session.close()
            raise HTTPException(status_code=404, detail="Employee not found")

        lendings = [
            {
                "id": lending.id,
                "assetDescription": lending.asset.description,
                "registerNumber": lending.asset.register_number,
                "serialNumber": lending.asset.serial_number,
                "msOffice": lending.asset.ms_office,
                "deleted": lending.deleted,
            }
            for lending in employee.lendings
        ]

        terms = [
            {
                "id": term.id,
                "description": term.term_item.description,
                "size": term.term_item.size,
                "quantity": term.term_item.quantity,
                "value": term.term_item.value,
                "operator": term.term_item.operator,
                "lineNumber": term.term_item.line_number,
                "type": term.type.name,
                "deleted": term.deleted,
            }
            for term in employee.terms
        ]

        return {
            "id": employee.id,
            "fullName": employee.full_name,
            "manager": employee.manager,
            "lendings": lendings,
            "terms": terms,
        }
