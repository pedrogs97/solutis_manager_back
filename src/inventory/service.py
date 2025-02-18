"""Inventory service"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Tuple

from fastapi import BackgroundTasks, HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import desc
from sqlalchemy.orm import Session, with_loader_criteria
from sqlalchemy.sql.expression import and_, or_

from src.backends import Email365Client, EmailQueue
from src.inventory.models import (
    InventoryExtraAssetModel,
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
                "executive": lending.business_executive,
                "location": lending.location,
                "costCenter": f"{lending.cost_center.name} / {lending.cost_center.code}",
                "bu": lending.bu,
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
            }
            for term in employee.terms
        ]

        employee_data = {
            "fullName": employee.full_name,
            "manager": employee.manager,
            "phone": employee.cell_phone,
            "email": employee.email,
            "lendings": lendings,
            "terms": terms,
        }

        token_data = {
            "employee_id": employee.id,
            "registration": employee.registration,
            "birthday": employee.birthday.strftime("%Y-%m-%d"),
        }

        return (employee_data, token_data)

    def __is_valid_lendings(
        self, employee_id: int, answer_lendings_ids: List[int]
    ) -> bool:
        """Validate lendings"""
        lendings = (
            self.db_session.query(LendingModel)
            .filter(LendingModel.employee_id == employee_id)
            .all()
        )

        if any(
            lending_id not in [lending.id for lending in lendings]
            for lending_id in answer_lendings_ids
        ):
            return False

        for lending in lendings:
            if lending.deleted:
                return False

        return True

    def __is_valid_terms(self, employee_id: int, answer_terms_ids: List[int]) -> bool:
        """Validate terms"""
        terms = (
            self.db_session.query(TermModel)
            .filter(TermModel.employee_id == employee_id)
            .all()
        )

        if any(
            term_id not in [term.id for term in terms] for term_id in answer_terms_ids
        ):
            return False

        for term in terms:
            if term.deleted:
                return False

        return True

    def __exists_answer_year(self, employee_id: int) -> bool:
        """Validate year"""
        currente_datetime = datetime.now()
        exists_inventory_answer = (
            self.db_session.query(InventoryModel)
            .filter(
                InventoryModel.employee_id == employee_id,
                InventoryModel.year == currente_datetime.year,
            )
            .exists()
        )

        return self.db_session.query(exists_inventory_answer).scalar()

    def create_invetory_answer(
        self, data: AnswerInventorySerializer, employee_id: int
    ) -> None:
        """Create inventory answer"""
        currente_datetime = datetime.now()

        if not self.__is_valid_lendings(
            employee_id, [lending.lending_id for lending in data.lendings]
        ):
            self.db_session.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comodatos inválidos. Contate o administrador",
            )

        if not self.__is_valid_terms(
            employee_id, [term.term_id for term in data.terms]
        ):
            self.db_session.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Termos inválidos. Contate o administrador",
            )

        if self.__exists_answer_year(employee_id):
            self.db_session.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um inventário para este ano",
            )

        inventory = InventoryModel(
            employee_id=employee_id,
            phone=data.phone,
            accepted_term_at=currente_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            year=currente_datetime.year,
            extra_items=data.extra_items,
        )
        self.db_session.add(inventory)
        self.db_session.commit()
        self.db_session.flush()

        for lending in data.lendings:
            inventory_lending = InventoryLendingModel(
                inventory_id=inventory.id,
                lending_id=lending.lending_id,
                justification=lending.justification,
                confirm=lending.confirm,
            )
            self.db_session.add(inventory_lending)

        for term in data.terms:
            inventory_term = InventoryTermModel(
                inventory_id=inventory.id,
                term_id=term.term_id,
                justification=term.justification,
                confirm=term.confirm,
            )
            self.db_session.add(inventory_term)

        for extra_asset in data.extra_assets:
            inventory_extra_asset = InventoryExtraAssetModel(
                inventory_id=inventory.id,
                register_number=extra_asset.register_number,
                description=extra_asset.description,
                serial_number=extra_asset.serial_number,
            )
            self.db_session.add(inventory_extra_asset)

        self.db_session.commit()
        logger.info(
            "Inventory answer created successfully - %s - Employee: %s",
            str(inventory),
            employee_id,
        )

    def get_answers(
        self, inventory_filter: dict, page: int = 1, size: int = 50
    ) -> Page[dict]:
        """Get answers"""

        employees_answer = (
            self.db_session.query(EmployeeModel)
            .outerjoin(InventoryModel)
            .outerjoin(InventoryLendingModel)
            .outerjoin(InventoryTermModel)
            .outerjoin(InventoryExtraAssetModel)
            .filter(EmployeeModel.status == "Ativo")
        )

        year_filter = inventory_filter.get("year")

        if not year_filter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ano é obrigatório",
            )

        for key, value in inventory_filter.items():
            if key == "employee_ids" and value:
                employees_answer = employees_answer.filter(EmployeeModel.id.in_(value))

            if key == "search" and value:
                employees_answer = employees_answer.filter(
                    or_(
                        EmployeeModel.full_name.ilike(f"%{value}%"),
                        EmployeeModel.registration.ilike(f"%{value}%"),
                    )
                )

            if key == "answered" and value is not None:
                if value:
                    employees_answer = employees_answer.filter(
                        InventoryModel.id.isnot(None),
                        InventoryModel.year == year_filter,
                    )
                else:
                    employees_answer = employees_answer.filter(
                        InventoryModel.id.is_(None)
                    )
            elif key == "has_extra" and value is not None:
                if value:
                    employees_answer = employees_answer.filter(
                        InventoryModel.id.isnot(None),
                        InventoryModel.year == year_filter,
                        or_(
                            InventoryModel.extra_items.isnot(None),
                            InventoryModel.extra_items != "",
                            InventoryExtraAssetModel.id.isnot(None),
                        ),
                    )
                else:
                    employees_answer = employees_answer.filter(
                        InventoryModel.id.isnot(None),
                        InventoryModel.year == year_filter,
                        or_(
                            InventoryModel.extra_items.is_(None),
                            InventoryModel.extra_items == "",
                            InventoryExtraAssetModel.id.is_(None),
                        ),
                    )

        employees_answer = employees_answer.order_by(desc(InventoryModel.created_at))
        # filtro pelo ano do inventário
        params = Params(page=page, size=size)
        paginated = paginate(
            employees_answer,
            params=params,
            transformer=lambda employees_list: [
                {
                    "employee": {
                        "fullName": employee.full_name,
                        "registration": employee.registration,
                        "phone": employee.cell_phone,
                        "email": employee.email,
                        "manager": employee.manager,
                    },
                    "lendings": [
                        {
                            "id": lending.lending.id,
                            "assetDescription": lending.lending.asset.description,
                            "registerNumber": lending.lending.asset.register_number,
                            "serialNumber": lending.lending.asset.serial_number,
                            "msOffice": lending.lending.asset.ms_office,
                            "executive": lending.lending.business_executive,
                            "location": lending.lending.location,
                            "costCenter": f"{lending.lending.cost_center.name} / {lending.lending.cost_center.code}",
                            "bu": lending.lending.bu,
                            "justification": lending.justification,
                            "confirm": lending.confirm,
                        }
                        for inventory in employee.inventories
                        if inventory.year == year_filter
                        for lending in inventory.lendings_answers
                    ],
                    "terms": [
                        {
                            "id": term.term.id,
                            "description": term.term.term_item.description,
                            "size": term.term.term_item.size,
                            "quantity": term.term.term_item.quantity,
                            "value": term.term.term_item.value,
                            "operator": term.term.term_item.operator,
                            "lineNumber": term.term.term_item.line_number,
                            "type": term.term.type.name,
                            "justification": term.justification,
                            "confirm": term.confirm,
                        }
                        for inventory in employee.inventories
                        if inventory.year == year_filter
                        for term in inventory.terms_answers
                    ],
                    "extraAssets": [
                        {
                            "id": extra_asset.id,
                            "registerNumber": extra_asset.register_number,
                            "description": extra_asset.description,
                            "serialNumber": extra_asset.serial_number,
                        }
                        for inventory in employee.inventories
                        if inventory.year == year_filter
                        for extra_asset in inventory.extra_assets
                    ],
                    "year": year_filter,
                    "extraItems": [
                        {
                            "extraItems": inventory.extra_items,
                        }
                        for inventory in employee.inventories
                        if inventory.year == year_filter
                    ],
                }
                for employee in employees_list
            ],
        )
        return paginated

    def get_employees_to_notify(self) -> List[dict]:
        """Get employees to notify"""
        # current_year = datetime.now().year
        # employees = (
        #     self.db_session.query(EmployeeModel)
        #     .outerjoin(InventoryModel)
        #     .filter(
        #         EmployeeModel.status == "Ativo",
        #         InventoryModel.id.is_(None),
        #         InventoryModel.year != current_year,
        #     )
        #     .all()
        # )

        # employees_to_notify = [
        #     {
        #         "email": employee.email,
        #         "full_name": employee.full_name,
        #     }
        #     for employee in employees
        # ]

        employees_to_notify = [
            {
                "email": "pedro.parametrize@gmail.com",
                "full_name": "Pedro Santana (Teste)",
            }
            # {
            #     "email": "brenner.pereira@solutis.com.br",
            #     "full_name": "Brenner Pereira (Teste)",
            # },
            # {
            #     "email": "carla.anunciacao@solutis.com.br",
            #     "full_name": "Carla Anunciação (Teste)",
            # },
            # {
            #     "email": "kecia.sousa@solutis.com.br",
            #     "full_name": "Kécia Sousa (Teste)",
            # },
            # {
            #     "email": "rodrigo.cavalcante@solutis.com.br",
            #     "full_name": "Rodrigo Cavalcante (Teste)",
            # },
            # {
            #     "email": "tailon.souza@solutis.com.br",
            #     "full_name": "Tailon Souza (Teste)",
            # },
            # {
            #     "email": "tais.santos@solutis.com.br",
            #     "full_name": "Tais Santos (Teste)",
            # },
            # {
            #     "email": "thomas.lichtenberger@solutis.com.br",
            #     "full_name": "Thomas Lichtenberger (Teste)",
            # },
            # {
            #     "email": "beatriz.cunha@solutis.com.br",
            #     "full_name": "Beatriz Cunha (Teste)",
            # },
            # {
            #     "email": "geovana.frutuoso@solutis.com.br",
            #     "full_name": "Geovana Frutuoso (Teste)",
            # },
            # {
            #     "email": "eliana.simoes@solutis.com.br",
            #     "full_name": "Eliana Simões (Teste)",
            # },
            # {
            #     "email": "claudia.cavalcante@solutis.com.br",
            #     "full_name": "Claudia Cavalcante (Teste)",
            # },
            # {
            #     "email": "magna.jesus@solutis.com.br",
            #     "full_name": "Magna Jesus (Teste)",
            # },
            # {
            #     "email": "emilie.bastos@solutis.com.br",
            #     "full_name": "Emilie Bastos (Teste)",
            # },
        ]

        return employees_to_notify

    async def process_email_queue(self, email_queue: EmailQueue):
        await email_queue.run()

    async def send_inventory_email(self):
        """Send inventory email"""
        try:
            email_queue = EmailQueue(max_workers=5)
            employees_to_notify = self.get_employees_to_notify()
            for employee in employees_to_notify:
                email_client = Email365Client(
                    mail_to=employee["email"],
                    mail_subject="Formulário de Inventário",
                    type_message="notify_inventory",
                    extra={"full_name": employee["full_name"]},
                )
                await email_queue.add_email_task(email_client, fake=False)

            BackgroundTasks.add_task(self.process_email_queue, email_queue)
        except Exception as error:
            logger.error("Error sending email: %s", error)
