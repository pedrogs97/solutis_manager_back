"""Report service"""

from typing import List

from openpyxl import Workbook
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.lending.models import LendingModel
from src.log.models import LogModel
from src.people.models import EmployeeModel


class ReportService:
    """Report service"""

    def __init__(self, by="employee") -> None:
        self.by = by

    def report_by_employee(
        self,
        start_date: str,
        end_date: str,
        employees: List[EmployeeModel],
        db_session: Session,
    ):
        """Report by employee"""
        columns = [
            "COLABORADOR",
            "CARGO",
            "PROJETO",
            "CENTRO DE CUSTO",
            "GESTOR",
            "EXECUTIVO",
            "LOCAL DE TRABALHO",
            "DESCRIÇÃO DO EQUIPAMENTO",
            "PATRIMÔNIO",
            "PADRÃO EQUIPAMENTO",
            "STATUS",
        ]
        previous_lending = (
            db_session.query(LogModel)
            .filter(
                LogModel.model == "Lending",
                LogModel.operation.startswith("Criação"),
                LogModel.logged_in.between(start_date, end_date),
            )
            .all()
        )
        report_data = (
            db_session.query(LendingModel)
            .filter(
                LendingModel.employee_id.in_([employee.id for employee in employees]),
                LendingModel.created_at.between(start_date, end_date),
                or_(LendingModel.id.in_([lending.id for lending in previous_lending])),
            )
            .all()
        )
        wb = Workbook()
        ws = wb.create_sheet("CONSULTA POR COLABORADOR")
        return report_data

    def report_by_asset(self):
        """Report by asset"""
        return self.by
