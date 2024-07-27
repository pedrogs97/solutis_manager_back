"""Report service"""

import io
import math
import os
import textwrap
from typing import List

from fastapi import HTTPException, status
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from reportlab.lib.pagesizes import inch, landscape, letter
from reportlab.pdfgen import canvas
from sqlalchemy import desc
from sqlalchemy.orm import Session
from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.utility import xl_rowcol_to_cell

from src.asset.models import AssetModel, AssetStatusHistoricModel
from src.config import DEFAULT_DATE_FORMAT, REPORT_UPLOAD_DIR
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
    MaintenanceReportFilter,
)


class ReportService:
    """Report service"""

    OFFSET_ROW = 7
    OFFSET_COL = 2
    LENDING_COLS = [
        ("C5", "COLABORADOR"),
        ("D5", "CARGO"),
        ("E5", "PROJETO"),
        ("E5", "BU"),
        ("F5", "CENTRO DE CUSTO"),
        ("F5", "CENTRO DE CUSTO (código)"),
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
        ("H5", "CENTRO DE CUSTO (código)"),
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
            "bu": lending.bu,
            "cost_center": (
                lending.cost_center.name if lending.cost_center else self.NOT_PROVIDED
            ),
            "cost_center_code": (
                lending.cost_center.code if lending.cost_center else self.NOT_PROVIDED
            ),
            "manager": lending.manager,
            "executive": lending.business_executive,
            "workload": lending.workload.name,
            "equipment_description": lending.asset.description,
            "patrimony": lending.asset.register_number,
            "equipment_standard": lending.asset.pattern,
            "status": lending.status.name,
        }

    def asset_to_report(self, asset: AssetModel, location: str, status) -> dict:
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
            "status": status,
        }

    def asset_pattern_to_report(self, asset: AssetModel, lending: LendingModel) -> dict:
        """Convert asset pattern to report"""
        return {
            "manager": lending.manager,
            "business_executive": lending.business_executive,
            "bu": lending.bu,
            "colaborador": (
                lending.employee.full_name if lending.employee else self.NOT_PROVIDED
            ),
            "pattern": asset.pattern if asset.pattern else self.NOT_PROVIDED,
            "cost_center": (
                lending.cost_center.name if lending.cost_center else self.NOT_PROVIDED
            ),
            "cost_center_code": (
                lending.cost_center.code if lending.cost_center else self.NOT_PROVIDED
            ),
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
        value = str(maintenance.asset.value).replace(".", ",")
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
            "value": f"R$ {value}",  # format value
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
        value = str(upgrade.asset.value).replace(".", ",")
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
            "value": f"R$ {value}",  # format value
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
                self.asset_to_report(data.asset, data.location, data.status.name)
                for data in report_list
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
                self.asset_to_report(
                    item.asset, item.location, item.status.name
                ).values()
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
            "CONSULTA PADRÃO DE EQUIPAMENTO",
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

    def report_by_maintenance(
        self, report_filters: MaintenanceReportFilter, db_session: Session
    ):
        """Report by maintenance"""
        report_data_maintenance = report_filters.filter_maintenance(
            db_session.query(MaintenanceHistoricModel), db_session.query(LogModel)
        ).all()
        report_data_upgrade = report_filters.filter_maintenance(
            db_session.query(UpgradeHistoricModel), db_session.query(LogModel)
        ).all()

        if not report_data_maintenance and not report_data_upgrade:
            return None

        if report_filters.maintenance_type is None:
            report_data = sorted(
                report_data_maintenance + report_data_upgrade, key=lambda x: x.date
            )
        elif report_filters.maintenance_type == "maintenance":
            report_data = sorted(report_data_maintenance, key=lambda x: x.date)
        elif report_filters.maintenance_type == "upgrade":
            report_data = sorted(report_data_upgrade, key=lambda x: x.date)
        else:
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
            values = (
                self.maintenance_to_report(item.maintenance).values()
                if hasattr(item, "maintenance")
                else self.upgrade_to_report(item.upgrade).values()
            )
            for i_col, value in enumerate(values):
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
        self,
        report_filters: MaintenanceReportFilter,
        db_session: Session,
        page: int = 1,
        size: int = 50,
    ):
        """Report list by maintenance"""
        report_data_maintenance_query = report_filters.filter_maintenance(
            db_session.query(MaintenanceHistoricModel), db_session.query(LogModel)
        )
        report_data_upgrade_query = report_filters.filter_maintenance(
            db_session.query(UpgradeHistoricModel), db_session.query(LogModel)
        )

        if not report_data_maintenance_query and not report_data_upgrade_query:
            return None

        if report_filters.maintenance_type is None:
            report_data = report_data_maintenance_query.union(report_data_upgrade_query)
        elif report_filters.maintenance_type == "maintenance":
            report_data = report_data_maintenance_query
        elif report_filters.maintenance_type == "upgrade":
            report_data = report_data_upgrade_query
        else:
            return None

        def transformer_report(data_list):
            data_list = sorted(data_list, key=lambda x: x.date)
            return [
                (
                    self.maintenance_to_report(data.maintenance)
                    if hasattr(data, "maintenance")
                    else self.upgrade_to_report(data.upgrade)
                )
                for data in data_list
            ]

        params = Params(page=page, size=size)
        paginated = paginate(
            report_data,
            params=params,
            transformer=transformer_report,
        )
        return paginated

    def __draw_wrapped_text(self, c: canvas.Canvas, text: str, y, max_width=80) -> int:
        wrapped_text = textwrap.wrap(text, width=max_width)
        line_height = 15
        line_offset = -15
        for i, line in enumerate(wrapped_text):
            c.drawString(0, y - i * line_height, line)
            line_offset = y - (i + 1) * line_height
        return line_offset

    def __draw_circle(self, c: canvas.Canvas, text: str, offset_image: int):
        c.setFillColorRGB(0.25, 0.91, 0.24)
        c.circle(inch, -1 * inch, inch, stroke=1, fill=1)
        c.setFillColor("black")
        wrapped_text = textwrap.wrap(text, width=20)
        line_height = 15
        for i, line in enumerate(wrapped_text):
            text_width = c.stringWidth(line, "Helvetica", 12)
            c.drawString(
                (2 * inch - text_width) / 2,
                -1 * inch - (line_height * i),
                line,
            )
        return offset_image + inch

    def __draw_rectangle(self, c: canvas.Canvas, text: str, offset_image: int):
        c.setFillColorRGB(0.96, 0.63, 0.99)
        c.rect(0, -1.5 * inch, 2 * inch, inch, stroke=1, fill=1)
        c.setFillColor("black")
        wrapped_text = textwrap.wrap(text, width=20)
        line_height = 15
        for i, line in enumerate(wrapped_text):
            text_width = c.stringWidth(line, "Helvetica", 12)
            c.drawString(
                (2 * inch - text_width) / 2,
                -0.8 * inch - (line_height * i),
                line,
            )
        return offset_image / 2.8

    def __draw_diamond(self, c: canvas.Canvas, text: str, offset_image: int):
        start_x = offset_image
        diamond_points = [
            (start_x + inch, 0),
            (start_x + 2 * inch, -1 * inch),
            (start_x + inch, -2 * inch),
            (start_x, -1 * inch),
        ]
        p = c.beginPath()
        p.moveTo(diamond_points[0][0], diamond_points[0][1])
        p.lineTo(diamond_points[1][0], diamond_points[1][1])
        p.lineTo(diamond_points[2][0], diamond_points[2][1])
        p.lineTo(diamond_points[3][0], diamond_points[3][1])
        p.close()
        c.setFillColorRGB(0.99, 0.91, 0.63)
        c.drawPath(p, stroke=1, fill=1)
        c.setFillColor("black")
        wrapped_text = textwrap.wrap(text, width=20)
        line_height = 15
        for i, line in enumerate(wrapped_text):
            text_width = c.stringWidth(line, "Helvetica", 12)
            c.drawString(
                (2 * (start_x + inch) - text_width) / 2,
                -1 * inch - (line_height * i),
                line,
            )
        return start_x + inch * 1.3

    def __draw_hexagon(self, c: canvas.Canvas, text: str, offset_image: int):
        center_x = offset_image + 2 * inch
        center_y = -1 * inch
        radius = 1 * inch
        hexagon_points = [
            (
                center_x + radius * math.cos(math.radians(angle)) * 1.5,
                center_y + radius * math.sin(math.radians(angle)) / 1.5,
            )
            for angle in range(0, 360, 60)
        ]
        p = c.beginPath()
        p.moveTo(hexagon_points[0][0], hexagon_points[0][1])
        for point in hexagon_points[1:]:
            p.lineTo(point[0], point[1])
        p.close()
        c.setFillColorRGB(0.69, 0.56, 0.44)
        c.drawPath(p, stroke=1, fill=1)
        c.setFillColor("black")
        wrapped_text = textwrap.wrap(text, width=10)
        line_height = 15
        for i, line in enumerate(wrapped_text):
            text_width = c.stringWidth(line, "Helvetica", 12)
            c.drawString(
                (3 * (inch + offset_image * 0.72) - text_width) / 2,
                -0.95 * inch - (line_height * i),
                line,
            )

        return offset_image + 6 * inch

    def __draw_shapes(
        self, c: canvas.Canvas, text: str, shape: str, x_offset: int, is_last: bool
    ) -> float:
        c.setFont("Helvetica", 12)
        c.saveState()
        c.translate(x_offset, -3 * inch)
        offset_image = x_offset
        if shape == "circle":
            offset_image = self.__draw_circle(c, text, offset_image)
        elif shape == "rectangle":
            offset_image = self.__draw_rectangle(c, text, offset_image)
        elif shape == "diamond":
            offset_image = self.__draw_diamond(c, text, offset_image)
        elif shape == "hexagon":
            offset_image = self.__draw_hexagon(c, text, offset_image)

        if not is_last:
            if shape == "circle":
                start_x = inch * 0.1 + offset_image
            elif shape == "diamond":
                start_x = offset_image * 0.61
            else:
                start_x = offset_image

            # Desenhar uma seta formada por uma linha e um triângulo alinhados
            c.translate(start_x, 0)
            start_y = -1 * inch
            length = 1.5 * inch  # Comprimento total da seta
            width = 0.15 * inch  # Largura da haste da seta

            # Desenhar a haste da seta (linha)
            line_length = length * 0.2
            c.setLineWidth(2)
            c.line(start_x, start_y, start_x + line_length, start_y)

            # Desenhar a ponta da seta (triângulo preenchido)
            triangle_base = width
            triangle_height = length * 0.2
            arrow_tip = [
                (start_x + line_length, start_y - triangle_base),
                (start_x + line_length + triangle_height, start_y),
                (start_x + line_length, start_y + triangle_base),
            ]

            # Usar path para criar e preencher o triângulo
            c.setFillColor("black")
            c.setStrokeColor("black")
            p = c.beginPath()
            p.moveTo(arrow_tip[0][0], arrow_tip[0][1])
            p.lineTo(arrow_tip[1][0], arrow_tip[1][1])
            p.lineTo(arrow_tip[2][0], arrow_tip[2][1])
            p.close()
            c.drawPath(p, stroke=1, fill=1)
            c.restoreState()
            if shape == "diamond":
                return offset_image * 0.92 + line_length + triangle_height + inch * 0.1
            return offset_image + start_x + line_length + triangle_height + inch * 0.35
        c.restoreState()
        return offset_image + inch * 3

    def report_asset_timeline(self, asset_id: int, db_session: Session):
        """Report asset timeline"""
        asset = db_session.query(AssetModel).filter(AssetModel.id == asset_id).first()
        historic = []
        if not asset:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "assetId", "error": "Equipamento não encontrado"},
            )

        filename = f"Fluxo Equipamento - {asset.register_number}.pdf"

        if not os.path.exists(REPORT_UPLOAD_DIR):
            os.mkdir(REPORT_UPLOAD_DIR)

        file_path = os.path.join(REPORT_UPLOAD_DIR, filename)
        c = canvas.Canvas(file_path, pagesize=landscape(letter))
        page_width, height = landscape(letter)
        c.translate(inch, height - inch)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(0, 0, "CONSULTA POR EQUIPAMENTO")
        c.setFont("Helvetica", 12)
        line_offset = self.__draw_wrapped_text(
            c, f"Descrição do equipamento: {asset.description}", -50
        )
        c.drawString(0, line_offset, f"Patrimônio: {asset.register_number}")
        serial_number = (
            asset.serial_number if asset.serial_number else self.NOT_PROVIDED
        )
        line_offset += -15
        c.drawString(0, line_offset, f"Número de série: {serial_number}")

        line_offset += -100
        acquisition_date = (
            asset.acquisition_date.strftime(DEFAULT_DATE_FORMAT)
            if asset.acquisition_date
            else self.NOT_PROVIDED
        )
        historic.append(
            {
                "date": acquisition_date,
                "text": "Aquisição em:",
                "type": "circle",
            }
        )
        historic_asset_status = (
            db_session.query(AssetStatusHistoricModel)
            .filter(AssetStatusHistoricModel.asset_id == asset_id)
            .order_by(AssetStatusHistoricModel.created_at)
            .all()
        )

        for historic_status in historic_asset_status:
            if historic_status.status_id in [1, 3, 4]:
                historic.append(
                    {
                        "date": historic_status.created_at.strftime(
                            DEFAULT_DATE_FORMAT
                        ),
                        "text": historic_status.status.name,
                        "type": "rectangle",
                    }
                )
            elif historic_status.status_id == 2:
                historic_lending = (
                    db_session.query(LendingModel)
                    .filter(
                        LendingModel.asset_id == asset_id,
                    )
                    .order_by(desc(LendingModel.created_at))
                    .first()
                )
                first_name = historic_lending.employee.full_name.split(" ")[0]
                last_name = historic_lending.employee.full_name.split(" ")[-1]
                historic.append(
                    {
                        "date": historic_status.created_at.strftime(
                            DEFAULT_DATE_FORMAT
                        ),
                        "text": f"Comodato \t {first_name} {last_name}",
                        "type": "rectangle",
                    }
                )
            elif historic_status.status_id == 9:
                historic.append(
                    {
                        "date": historic_status.created_at.strftime(
                            DEFAULT_DATE_FORMAT
                        ),
                        "text": historic_status.status.name,
                        "type": "diamond",
                    }
                )
            elif historic_status.status_id == 10:
                historic.append(
                    {
                        "date": historic_status.created_at.strftime(
                            DEFAULT_DATE_FORMAT
                        ),
                        "text": historic_status.status.name,
                        "type": "hexagon",
                    }
                )
            elif historic_asset_status in [6, 8]:
                historic.append(
                    {
                        "date": historic_status.created_at.strftime(
                            DEFAULT_DATE_FORMAT
                        ),
                        "text": historic_status.status.name,
                        "type": "circle",
                    }
                )

        offset = 0
        last_index = len(historic) - 1
        for index, h in enumerate(historic):
            text = h["text"]
            date = h["date"]
            offset = self.__draw_shapes(
                c, f"{text} {date}", h["type"], offset, index == last_index
            )
            if offset >= page_width - 4 * inch:
                page_width = page_width + 6.5 * inch
                c.setPageSize((page_width, landscape(letter)[1]))

        c.showPage()
        c.save()
        return (file_path, filename)
