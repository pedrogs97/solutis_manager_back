"""Invoice service"""

import logging
import os
from datetime import date

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.asset.models import AssetModel
from src.asset.schemas import AssetShortSerializerSchema
from src.auth.models import UserModel
from src.config import BASE_DIR, DEBUG, DEFAULT_DATE_FORMAT, MEDIA_UPLOAD_DIR
from src.invoice.filters import InvoiceFilter
from src.invoice.models import InvoiceModel
from src.invoice.schemas import InvoiceSerializerSchema, NewInvoiceSchema
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
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "invoice", "error": "Nota fiscal não encontrada"},
            )

        return invoice

    def __get_asset_or_404(self, asset_id: int, db_session: Session) -> AssetModel:
        """Get asset or 404"""
        asset = db_session.query(AssetModel).filter(AssetModel.id == asset_id).first()

        if not asset:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "assetId", "error": "Ativo não encontrado"},
            )

        return asset

    def serialize_invoice(self, invoice: InvoiceModel) -> InvoiceSerializerSchema:
        """Serialize invoice"""

        assets = [
            AssetShortSerializerSchema(
                id=asset.id,
                asset_type=asset.type.name if asset.type else None,
                description=asset.description,
                register_number=asset.register_number,
                value=asset.value,
            )
            for asset in invoice.assets
        ]

        return InvoiceSerializerSchema(
            id=invoice.id,
            number=invoice.number,
            path=invoice.path,
            file_name=invoice.file_name,
            assets=assets,
            deleted_at=(
                invoice.deleted_at.strftime(DEFAULT_DATE_FORMAT)
                if invoice.deleted_at
                else None
            ),
        )

    def create_invoice(
        self,
        data: NewInvoiceSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> InvoiceSerializerSchema:
        """Creates new invoice"""

        assets_db = []
        for asset_id in data.assets_id:
            assets_db.append(self.__get_asset_or_404(asset_id, db_session))

        new_invoice_db = InvoiceModel(number=data.number)
        new_invoice_db.assets = assets_db

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

        logger.info("New Invoice. %s", str(new_invoice_db))

        return self.serialize_invoice(new_invoice_db)

    async def upload_document_invoice(
        self,
        invoice: int,
        invoice_file: UploadFile,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> InvoiceSerializerSchema:
        """Upload document invoice"""

        invoice_db = self.__get_invoice_or_404(invoice, db_session)

        code = invoice_db.number

        file_name = f"{code}.pdf"

        upload_dir = (
            os.path.join(BASE_DIR, "storage", "media") if DEBUG else MEDIA_UPLOAD_DIR
        )

        file_path = await upload_file(
            file_name, "invoice", invoice_file.file.read(), upload_dir
        )

        invoice_db.path = file_path
        invoice_db.file_name = file_name

        db_session.add(invoice_db)
        db_session.commit()

        service_log.set_log(
            "invoice",
            "asset",
            "Atualização de Nota Fiscal",
            invoice_db.id,
            authenticated_user,
            db_session,
        )

        service_log.set_log(
            "invoice",
            "invoice",
            "Importação de Nota Fiscal",
            invoice_db.id,
            authenticated_user,
            db_session,
        )

        logger.info("Update Invoice. %s", str(invoice_db))

        return self.serialize_invoice(invoice_db)

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
        deleted: int = 0,
    ) -> Page[InvoiceSerializerSchema]:
        """Get invoices list"""
        invoice_list_query = db_session.query(InvoiceModel)
        if not deleted:
            invoice_list_query = invoice_filters.filter(
                invoice_list_query.filter(InvoiceModel.deleted_at.is_(None))
            ).order_by(desc(InvoiceModel.id))
        else:
            invoice_list_query = invoice_filters.filter(
                invoice_list_query.filter(InvoiceModel.deleted_at.is_not(None))
            ).order_by(desc(InvoiceModel.id))

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
