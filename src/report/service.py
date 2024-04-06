"""Report service"""

import io
from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Session
from xlsxwriter import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell

from src.lending.models import LendingModel
from src.lending.service import LendingService
from src.log.models import LogModel
from src.people.models import EmployeeModel


class ReportService:
    """Report service"""

    OFFSET_ROW = 7
    OFFSET_COL = 1

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
            ("C5", "COLABORADOR"),
            ("D5", "CARGO"),
            ("E5", "PROJETO"),
            ("F5", "CENTRO DE CUSTO"),
            ("G5", "GESTOR"),
            ("H5", "EXECUTIVO"),
            ("I5", "LOCAL DE TRABALHO"),
            ("J5", "DESCRIÇÃO DO EQUIPAMENTO"),
            ("K5", "PATRIMÔNIO"),
            ("L5", "PADRÃO EQUIPAMENTO"),
            ("M5", "STATUS"),
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
        output_file = io.BytesIO()
        workbook = Workbook(output_file)
        worksheet = workbook.add_worksheet("CONSULTA POR COLABORADOR")
        worksheet.hide_gridlines(2)
        cell_title_format = workbook.add_format()
        cell_title_format.set_align("center")
        cell_title_format.set_border(1)
        cell_title_format.set_bold()
        cell_title_format.set_border_color("black")
        cell_title_format.set_font("Calibri")
        cell_title_format.set_font_size(12)

        worksheet.write("C3", "CONSULTA POR COLABORADOR", cell_title_format)

        cell_col_header_format = workbook.add_format()
        cell_col_header_format.set_align("center")
        cell_col_header_format.set_border(1)
        cell_col_header_format.set_bold()
        cell_col_header_format.set_border_color("black")
        cell_col_header_format.set_font("Calibri")
        cell_col_header_format.set_bg_color("#BFBFBF")
        cell_col_header_format.set_font_color("black")
        cell_col_header_format.set_font_size(11)

        for col in columns:
            worksheet.write(col[0], col[1], cell_col_header_format)

        cell_data_format = workbook.add_format()
        cell_data_format.set_border(1)
        cell_data_format.set_num_format("d/mm/yyyy")
        cell_col_header_format.set_font("Aptos Narrow")
        cell_col_header_format.set_font_size(11)

        lending_service = LendingService()
        serialized_report_data = [
            lending_service.serialize_lending(report).model_dump(by_alias=False)
            for report in report_data
        ]

        for i_row, item in enumerate(serialized_report_data):
            for i_col, entry in enumerate(item.items()):
                worksheet.write(
                    xl_rowcol_to_cell(i_row + self.OFFSET_ROW, i_col + self.OFFSET_COL),
                    entry,
                    cell_data_format,
                )

        worksheet.autofit()
        workbook.close()
        output_file.seek(0)
        with open("report.xlsx", "wb") as file:
            file.write(output_file.read())
        return report_data

    def report_by_asset(self):
        """Report by asset"""
        return self.by
