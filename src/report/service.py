"""Report service"""

import io
from typing import List

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.utility import xl_rowcol_to_cell

from src.asset.models import AssetModel
from src.lending.models import LendingModel
from src.log.models import LogModel
from src.maintenance.models import (
    MaintenanceHistoricModel,
    MaintenanceModel,
    UpgradeHistoricModel,
    UpgradeModel,
)
from src.report.filters import (
    AssetPatternFilter,
    AssetReportFilter,
    LendingReportFilter,
)


class ReportService:
    """Report service"""

    OFFSET_ROW = 7
    OFFSET_COL = 2
    LENDING_COLS = [
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

    ASSET_COLS = [
        ("C5", "DESCRIÇÃO DO EQUIPAMENTO"),
        ("D5", "PATRIMÔNIO"),
        ("E5", "NÚMERO DE SÉRIE / IMEI"),
        ("F5", "PADRÃO EQUIPAMENTO"),
        ("G5", "LOCALIZAÇÃO"),
        ("H5", "DATA DE AQUISIÇÃO"),
        ("I5", "NÚMERO NF"),
        ("J5", "GARANTIA"),
        ("K5", "VALOR"),
        ("L5", "VALOR COM DEPRECIAÇÃO"),
        ("M5", "ITEMS ANEXADOS"),
        ("N5", "STATUS"),
    ]

    ASSET_PATTERN_COLS = [
        ("C5", "GESTOR"),
        ("D5", "EXECUTIVO"),
        ("E5", "BU"),
        ("F5", "COLABORADOR"),
        ("G5", "PADRÃO EQUIPAMENTO"),
        ("H5", "CENTRO DE CUSTO"),
        ("I5", "DESCRIÇÃO DO EQUIPAMENTO"),
        ("J5", "PATRIMÔNIO"),
        ("K5", "TIPO DE CONTRATO"),
    ]

    MAINTENANCE_COLS = [
        ("C5", "DATA DA ABERTURA DO CHAMADO"),
        ("D5", "DATA DE ENCERRAMENTO DO CHAMADO"),
        ("E5", "NÚMERO DO CHAMADO"),
        ("F5", "TIPO DE INCIDENTE"),
        ("G5", "DESCRIÇÃO DO INCIDENTE/MELHORIA"),
        ("H5", "DESCRIÇÃO DO EQUIPAMENTO"),
        ("I5", "NÚMERO DE SÉRIE / IMEI"),
        ("J5", "PATRIMÔNIO"),
        ("K5", "PADRÃO DO EQUIPAMENTO"),
        ("L5", "GARANTIA"),
        ("M5", "VALOR (R$)"),
        ("N5", "STATUS"),
    ]

    REPORT_FILE_NAME = "report.xlsx"

    NOT_PROVIDED = "Não informado"

    def __init__(self, by="CONSULTA POR COLABORADOR") -> None:
        self.output_file = io.BytesIO()
        self.workbook = Workbook(self.output_file)
        self.worksheet = self.workbook.add_worksheet(by)

    def lending_to_report(self, lending: LendingModel) -> dict:
        """Convert lending to report"""
        return {
            "employee": lending.employee.full_name,
            "role": lending.employee.role.name,
            "project": lending.project,
            "cost_center": lending.cost_center.name,
            "manager": lending.manager,
            "executive": lending.business_executive,
            "workload": lending.workload.name,
            "equipment_description": lending.asset.description,
            "patrimony": lending.asset.register_number,
            "equipment_standard": lending.asset.pattern,
            "status": lending.status.name,
        }

    def asset_to_report(self, asset: AssetModel, location: str) -> dict:
        """Convert asset to report"""
        return {
            "description": asset.description,
            "register_number": asset.register_number,
            "serial_number": f"{asset.serial_number} / {asset.imei}",
            "pattern": asset.pattern,
            "location": location,
            "acquisition_date": (
                asset.acquisition_date if asset.acquisition_date else self.NOT_PROVIDED
            ),
            "invoice": asset.invoice.number if asset.invoice else self.NOT_PROVIDED,
            "assurance_date": (
                asset.assurance_date if asset.assurance_date else self.NOT_PROVIDED
            ),
            "value": f"{asset.value:.2f}",
            "depreciation": asset.depreciation,
            "attachments": "-",
            "status": asset.status.name if asset.status else self.NOT_PROVIDED,
        }

    def asset_pattern_to_report(self, asset: AssetModel, lending: LendingModel) -> dict:
        """Convert asset pattern to report"""
        return {
            "manager": lending.manager,
            "business_executive": lending.business_executive,
            "bu": lending.bu,
            "colaborador": lending.employee.full_name,
            "pattern": asset.pattern if asset.pattern else self.NOT_PROVIDED,
            "cost_center": lending.cost_center.name,
            "description": asset.description,
            "register_number": asset.register_number,
            "type": asset.type.name if asset.type else self.NOT_PROVIDED,
        }

    def maintenance_to_report(self, maintenance: MaintenanceModel) -> dict:
        """Convert maintenance to report"""
        serial_number = (
            maintenance.asset.serial_number
            if maintenance.asset.serial_number
            else self.NOT_PROVIDED
        )
        imei = maintenance.asset.imei if maintenance.asset.imei else self.NOT_PROVIDED
        return {
            "opening_date": maintenance.open_date,
            "closing_date": maintenance.close_date,
            "call_number": (
                maintenance.glpi_number
                if maintenance.glpi_number
                else self.NOT_PROVIDED
            ),
            "incident_type": "MANUTENÇÃO",
            "description": maintenance.resolution,
            "equipment_description": maintenance.asset.description,
            "serial_number": f"{serial_number} / {imei}",
            "patrimony": maintenance.asset.register_number,
            "pattern": maintenance.asset.pattern,
            "assurance_date": maintenance.asset.assurance_date,
            "value": str(maintenance.asset.value).replace(".", ","),  # format value
            "status": maintenance.status.name,
        }

    def upgrade_to_report(self, upgrade: UpgradeModel) -> dict:
        """Convert upgrade to report"""
        serial_number = (
            upgrade.asset.serial_number
            if upgrade.asset.serial_number
            else self.NOT_PROVIDED
        )
        imei = upgrade.asset.imei if upgrade.asset.imei else self.NOT_PROVIDED
        return {
            "opening_date": upgrade.open_date,
            "closing_date": upgrade.close_date,
            "call_number": self.NOT_PROVIDED,
            "incident_type": "MELHORIA",
            "description": upgrade.detailing,
            "equipment_description": upgrade.asset.description,
            "serial_number": f"{serial_number} / {imei}",
            "patrimony": upgrade.asset.register_number,
            "pattern": upgrade.asset.pattern,
            "assurance_date": upgrade.asset.assurance_date,
            "value": upgrade.asset.value,
            "status": upgrade.status.name,
        }

    def __format_cell(self, cell_format: Format) -> Format:
        """Format cell"""
        cell_format.set_border(1)
        cell_format.set_num_format("d/mm/yyyy")
        cell_format.set_font("Aptos Narrow")
        cell_format.set_font_size(11)
        return cell_format

    def __format_cell_title(self, cell_format: Format) -> Format:
        """Format cell title"""
        cell_format.set_align("center")
        cell_format.set_border(1)
        cell_format.set_bold()
        cell_format.set_border_color("black")
        cell_format.set_font("Calibri")
        cell_format.set_font_size(12)
        return cell_format

    def __format_cell_col(self, cell_format: Format) -> Format:
        """Format cell col"""
        cell_format.set_align("center")
        cell_format.set_border(1)
        cell_format.set_bold()
        cell_format.set_border_color("black")
        cell_format.set_font("Calibri")
        cell_format.set_bg_color("#BFBFBF")
        cell_format.set_font_color("black")
        cell_format.set_font_size(11)
        return cell_format

    def report_list_by_employee(
        self,
        report_filters: LendingReportFilter,
        db_session: Session,
        page: int = 1,
        size: int = 50,
    ):
        """Report list by employee"""
        report_list = report_filters.filter(
            db_session.query(LendingModel), db_session.query(LogModel)
        )
        params = Params(page=page, size=size)
        paginated = paginate(
            report_list,
            params=params,
            transformer=lambda report_list: [
                self.lending_to_report(data) for data in report_list
            ],
        )
        return paginated

    def report_by_employee(
        self,
        report_filters: LendingReportFilter,
        db_session: Session,
    ):
        """Report by employee"""
        report_data = report_filters.filter(
            db_session.query(LendingModel), db_session.query(LogModel)
        ).all()

        if not report_data:
            return None

        self.worksheet.hide_gridlines(2)

        self.worksheet.write(
            "C3",
            "CONSULTA POR COLABORADOR",
            self.__format_cell_title(self.workbook.add_format()),
        )

        cell_col_header_format = self.__format_cell_col(self.workbook.add_format())

        for col in self.LENDING_COLS:
            self.worksheet.write(col[0], col[1], cell_col_header_format)

        cell_data_format = self.__format_cell(self.workbook.add_format())

        for i_row, item in enumerate(report_data):
            for i_col, value in enumerate(self.lending_to_report(item).values()):
                self.worksheet.write(
                    xl_rowcol_to_cell(i_row + self.OFFSET_ROW, i_col + self.OFFSET_COL),
                    value,
                    cell_data_format,
                )

        self.worksheet.autofit()
        self.workbook.close()
        self.output_file.seek(0)
        return self.output_file

    def report_list_by_asset(
        self,
        report_filters: AssetReportFilter,
        db_session: Session,
        page: int = 1,
        size: int = 50,
    ):
        """Report list by asset"""
        report_list = report_filters.filter(
            db_session.query(LendingModel), db_session.query(LogModel)
        )
        params = Params(page=page, size=size)
        paginated = paginate(
            report_list,
            params=params,
            transformer=lambda report_list: [
                self.asset_to_report(data.asset, data.location) for data in report_list
            ],
        )
        return paginated

    def report_by_asset(
        self,
        report_filters: AssetReportFilter,
        db_session: Session,
    ):
        """Report by asset"""
        report_data: List[LendingModel] = report_filters.filter(
            db_session.query(LendingModel), db_session.query(LogModel)
        ).all()

        if not report_data:
            return None

        self.worksheet.hide_gridlines(2)

        self.worksheet.write(
            "C3",
            "CONSULTA POR EQUIPAMENTO",
            self.__format_cell_title(self.workbook.add_format()),
        )

        cell_col_header_format = self.__format_cell_col(self.workbook.add_format())

        for col in self.ASSET_COLS:
            self.worksheet.write(col[0], col[1], cell_col_header_format)

        cell_data_format = self.__format_cell(self.workbook.add_format())

        for i_row, item in enumerate(report_data):
            for i_col, value in enumerate(
                self.asset_to_report(item.asset, item.location).values()
            ):
                self.worksheet.write(
                    xl_rowcol_to_cell(i_row + self.OFFSET_ROW, i_col + self.OFFSET_COL),
                    value,
                    cell_data_format,
                )

        self.worksheet.autofit()
        self.workbook.close()
        self.output_file.seek(0)
        return self.output_file

    def report_list_by_asset_pattern(
        self,
        report_filters: AssetPatternFilter,
        db_session: Session,
        page: int = 1,
        size: int = 50,
    ):
        """Report list by asset_pattern"""
        report_list = report_filters.filter(
            db_session.query(LendingModel), db_session.query(LogModel)
        )

        params = Params(page=page, size=size)
        paginated = paginate(
            report_list,
            params=params,
            transformer=lambda report_list: [
                self.asset_pattern_to_report(data.asset, data) for data in report_list
            ],
        )
        return paginated

    def report_by_asset_pattern(
        self,
        report_filters: AssetPatternFilter,
        db_session: Session,
    ):
        """Report by asset"""
        report_data: List[LendingModel] = report_filters.filter(
            db_session.query(LendingModel), db_session.query(LogModel)
        ).all()

        if not report_data:
            return None

        self.worksheet.hide_gridlines(2)

        self.worksheet.write(
            "C3",
            "CONSULTA POR PADRÃO DE EQUIPAMENTO",
            self.__format_cell_title(self.workbook.add_format()),
        )

        cell_col_header_format = self.__format_cell_col(self.workbook.add_format())

        for col in self.ASSET_COLS:
            self.worksheet.write(col[0], col[1], cell_col_header_format)

        cell_data_format = self.__format_cell(self.workbook.add_format())

        for i_row, item in enumerate(report_data):
            for i_col, value in enumerate(
                self.asset_pattern_to_report(item.asset, item).values()
            ):
                self.worksheet.write(
                    xl_rowcol_to_cell(i_row + self.OFFSET_ROW, i_col + self.OFFSET_COL),
                    value,
                    cell_data_format,
                )

        self.worksheet.autofit()
        self.workbook.close()
        self.output_file.seek(0)
        return self.output_file

    def report_by_maintenance(self, db_session: Session):
        """Report by maintenance"""
        report_data = (
            db_session.query(MaintenanceHistoricModel)
            .union(db_session.query(UpgradeHistoricModel))
            .all()
        )

        if not report_data:
            return None

        self.worksheet.hide_gridlines(2)

        self.worksheet.write(
            "C3",
            "CONSULTA POR MANUTENÇÃO / MELHORIA",
            self.__format_cell_title(self.workbook.add_format()),
        )

        cell_col_header_format = self.__format_cell_col(self.workbook.add_format())

        for col in self.MAINTENANCE_COLS:
            self.worksheet.write(col[0], col[1], cell_col_header_format)

        cell_data_format = self.__format_cell(self.workbook.add_format())

        for i_row, item in enumerate(report_data):
            for i_col, value in enumerate(
                self.maintenance_to_report(item.maintenance).values()
            ):
                self.worksheet.write(
                    xl_rowcol_to_cell(i_row + self.OFFSET_ROW, i_col + self.OFFSET_COL),
                    value,
                    cell_data_format,
                )

        self.worksheet.autofit()
        self.workbook.close()
        self.output_file.seek(0)
        return self.output_file

    def report_list_by_maintenance(
        self, db_session: Session, page: int = 1, size: int = 50
    ):
        """Report list by maintenance"""
        report_data = db_session.query(MaintenanceHistoricModel).union(
            db_session.query(UpgradeHistoricModel)
        )
        params = Params(page=page, size=size)
        paginated = paginate(
            report_data,
            params=params,
            transformer=lambda report_list: [
                self.maintenance_to_report(data.maintenance) for data in report_list
            ],
        )
        return paginated
