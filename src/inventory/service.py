"""Inventory service"""

import logging
import traceback
from datetime import datetime
from typing import Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session, with_loader_criteria

from src.inventory.models import (
    InventoryExtraAssetModel,
    InventoryExtraItemModel,
    InventoryLendingModel,
    InventoryModel,
    InventoryTermModel,
)
from src.inventory.schemas import AnswerInventorySerializer, EmployeeInventorySerializer
from src.lending.models import LendingModel
from src.people.models import EmployeeModel
from src.term.models import TermModel

logger = logging.getLogger(__name__)


class InventoryService:
    """Inventory service"""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_employee(self, data: EmployeeInventorySerializer) -> Tuple:
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

        employee_data = {
            "fullName": employee.full_name,
            "manager": employee.manager,
            "lendings": lendings,
            "terms": terms,
        }

        token_data = {
            "employee_id": employee.id,
            "registration": employee.registration,
            "birthday": employee.birthday.strftime("%Y-%m-%d"),
        }

        return (employee_data, token_data)

    def create_invetory_answer(
        self, data: AnswerInventorySerializer, employee_id: int
    ) -> None:
        """Create inventory answer"""
        try:
            currente_datetime = datetime.now()
            inventory = InventoryModel(
                employee_id=employee_id,
                phone=data.phone,
                accepted_term_at=currente_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                year=currente_datetime.year,
            )
            self.db_session.add(inventory)
            self.db_session.commit()
            self.db_session.flush()

            for lending in data.lendings:
                inventory_lending = InventoryLendingModel(
                    inventory_id=inventory.id,
                    lending_id=lending["id"],
                    justification=lending["justification"],
                    confirm=lending["confirm"],
                )
                self.db_session.add(inventory_lending)

            for term in data.terms:
                inventory_term = InventoryTermModel(
                    inventory_id=inventory.id,
                    term_id=term["id"],
                    justification=term["justification"],
                    confirm=term["confirm"],
                )
                self.db_session.add(inventory_term)

            for extra_asset in data.extra_assets:
                inventory_extra_asset = InventoryExtraAssetModel(
                    inventory_id=inventory.id,
                    register_number=extra_asset["registerNumber"],
                    description=extra_asset["description"],
                    serial_number=extra_asset["serialNumber"],
                )
                self.db_session.add(inventory_extra_asset)

            for extra_item in data.extra_items:
                inventory_extra_item = InventoryExtraItemModel(
                    inventory_id=inventory.id,
                    description=extra_item["description"],
                )
                self.db_session.add(inventory_extra_item)

            self.db_session.commit()
            logger.info("Inventory answer created successfully - %s", str(inventory))
        except Exception as error:
            self.db_session.rollback()
            self.db_session.close()
            exc_message = traceback.format_exc()
            error_message = f"Error creating inventory answer: {exc_message}"
            logger.error(error_message)
            raise HTTPException(status_code=500, detail=str(error))
