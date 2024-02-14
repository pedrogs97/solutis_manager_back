"""Invoice service"""

import logging
import os
from datetime import date
from typing import List

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.asset.models import AssetModel
from src.asset.schemas import AssetShortSerializerSchema
from src.auth.models import UserModel
from src.config import BASE_DIR, DEBUG, DEFAULT_DATE_FORMAT, MEDIA_UPLOAD_DIR
from src.invoice.filters import InvoiceFilter
from src.invoice.models import InvoiceModel
from src.invoice.schemas import InvoiceSerializerSchema
from src.log.services import LogService
from src.utils import upload_file

logger = logging.getLogger(__name__)
service_log = LogService()


class InvoiceService:
    """Invoice services"""

    def __get_invoice_or_404(
        self, invoice_id: int, db_session: Session
    ) -> InvoiceModel:
        """Get invoice or 404"""
        invoice = (
            db_session.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "invoice", "error": "Nota fiscal não encontrada"},
            )

        return invoice

    def __get_asset_or_404(self, asset_id: int, db_session: Session) -> AssetModel:
        """Get asset or 404"""
        asset = db_session.query(AssetModel).filter(AssetModel.id == asset_id).first()

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "assetId", "error": "Ativo não encontrado"},
            )

        return asset

    def serialize_invoice(self, invoice: InvoiceModel) -> InvoiceSerializerSchema:
        """Serialize invoice"""

        return InvoiceSerializerSchema(
            id=invoice.id,
            number=invoice.number,
            path=invoice.path,
            file_name=invoice.file_name,
            asset=AssetShortSerializerSchema(
                id=invoice.asset.id,
                asset_type=invoice.asset.type.name,
                description=invoice.asset.description,
                register_number=invoice.asset.register_number,
            ),
            deleted_at=(
                invoice.deleted_at.strftime(DEFAULT_DATE_FORMAT)
                if invoice.deleted_at
                else None
            ),
        )

    async def create_invoice(
        self,
        assets_id: List[int],
        number: str,
        invoice_file: UploadFile,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> InvoiceSerializerSchema:
        """Creates new invoice"""

        assets_db = []
        for asset_id in assets_id:
            assets_db.append(self.__get_asset_or_404(asset_id, db_session))

        new_invoice_db = InvoiceModel(number=number)
        new_invoice_db.assets = assets_db

        code = new_invoice_db.number

        file_name = f"{code}.pdf"

        upload_dir = (
            os.path.join(BASE_DIR, "storage", "media") if DEBUG else MEDIA_UPLOAD_DIR
        )

        file_path = await upload_file(
            file_name, "invoice", invoice_file.file.read(), upload_dir
        )

        new_invoice_db.path = file_path
        new_invoice_db.file_name = file_name

        db_session.add(new_invoice_db)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "invoice",
            "asset",
            "Criação de Nota Fiscal",
            new_invoice_db.id,
            authenticated_user,
            db_session,
        )

        service_log.set_log(
            "invoice",
            "invoice",
            "Importação de Nota Fiscal",
            new_invoice_db.id,
            authenticated_user,
            db_session,
        )

        logger.info("New Invoice. %s", str(new_invoice_db))

        return self.serialize_invoice(new_invoice_db)

    def get_invoice(
        self, invoice_id: int, db_session: Session
    ) -> InvoiceSerializerSchema:
        """Get a invoice"""
        invoice = self.__get_invoice_or_404(invoice_id, db_session)
        return self.serialize_invoice(invoice)

    def delete_invoice(
        self, invoice_id: int, db_session: Session
    ) -> InvoiceSerializerSchema:
        """Get a invoice"""
        invoice = self.__get_invoice_or_404(invoice_id, db_session)
        invoice.deleted_at = date.today()
        db_session.add(invoice)
        db_session.commit()
        return self.serialize_invoice(invoice)

    def get_invoices(
        self,
        db_session: Session,
        invoice_filters: InvoiceFilter,
        page: int = 1,
        size: int = 50,
        deleted: bool = False,
    ) -> Page[InvoiceSerializerSchema]:
        """Get invoices list"""
        if not deleted:
            invoice_list_query = invoice_filters.filter(
                db_session.query(InvoiceModel).filter(
                    InvoiceModel.deleted_at.is_not(None)
                )
            )
        else:
            invoice_list_query = invoice_filters.filter(db_session.query(InvoiceModel))

        params = Params(page=page, size=size)
        paginated = paginate(
            invoice_list_query,
            params=params,
            transformer=lambda invoice_list_query: [
                self.serialize_invoice(invoice).model_dump(by_alias=True)
                for invoice in invoice_list_query
            ],
        )
        return paginated
