"""Invoice service"""
import logging
import os

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.asset.models import AssetModel
from src.asset.schemas import AssetSerializerSchema
from src.auth.models import UserModel
from src.config import BASE_DIR, DEBUG, MEDIA_UPLOAD_DIR
from src.invoice.filters import InvoiceFilter
from src.invoice.models import InvoiceAssets, InvoiceModel
from src.invoice.schemas import (
    AssetInvoiceSerializerSchema,
    InvoiceSerializerSchema,
    NewInvoiceSchema,
    UploadInvoiceSchema,
)
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

    def __validate_nested(self, data: NewInvoiceSchema, db_session: Session) -> None:
        """Validate asstes"""
        if data.assets:
            error_ids = []
            for asset_invoice in data.assets:
                asset = (
                    db_session.query(AssetModel)
                    .filter(AssetModel.id == asset_invoice.asset_id)
                    .first()
                )
                if not asset:
                    error_ids.append(asset_invoice.asset_id)

            if error_ids:
                errors = {
                    "field": "assets",
                    "error": {"error": "Ativos não existem", "ids": error_ids},
                }
                raise HTTPException(
                    detail=errors,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

    def serialize_invoice(self, invoice: InvoiceModel) -> InvoiceSerializerSchema:
        """Serialize invoice"""

        assets = [
            AssetInvoiceSerializerSchema(**asset.__dict__) for asset in invoice.assets
        ]
        return InvoiceSerializerSchema(**{**invoice.__dict__, "assets_invoice": assets})

    def create_invoice(
        self,
        new_invoice: NewInvoiceSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> InvoiceSerializerSchema:
        """Creates new invoice"""

        self.__validate_nested(new_invoice, db_session)

        new_invoice_db = InvoiceModel(
            **new_invoice.model_dump(by_alias=False, exclude={"assets"})
        )
        db_session.add(new_invoice_db)
        db_session.commit()
        db_session.flush()

        for invoice_asset in new_invoice.assets:
            new_invoice_asset = InvoiceAssets(
                **{
                    **invoice_asset.model_dump(by_alias=False, exclude={"asset_id"}),
                    "asset_id": invoice_asset.asset_id,
                    "invoice_id": new_invoice_db.id,
                }
            )
            db_session.add(new_invoice_asset)
            db_session.commit()

        db_session.commit()
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

    def get_invoice(
        self, invoice_id: int, db_session: Session
    ) -> InvoiceSerializerSchema:
        """Get a invoice"""
        invoice = self.__get_invoice_or_404(invoice_id, db_session)
        return self.serialize_invoice(invoice)

    def get_invoices(
        self,
        db_session: Session,
        invoice_filters: InvoiceFilter,
        page: int = 1,
        size: int = 50,
    ) -> Page[AssetSerializerSchema]:
        """Get invoices list"""
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

    async def upload_invoice(
        self,
        invoice_file: UploadFile,
        data: UploadInvoiceSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> InvoiceSerializerSchema:
        """Upload invoice"""

        invoice = self.__get_invoice_or_404(data.invoice_id, db_session)

        code = invoice.number

        file_name = f"{code}.pdf"

        upload_dir = (
            os.path.join(BASE_DIR, "storage", "media") if DEBUG else MEDIA_UPLOAD_DIR
        )

        file_path = await upload_file(
            file_name, "invoice", invoice_file.file.read(), upload_dir
        )

        invoice.path = file_path
        invoice.file_name = file_name

        db_session.add(invoice)
        db_session.commit()

        service_log.set_log(
            "invoice",
            "invoice",
            "Importação de Nota Fiscal",
            invoice.id,
            authenticated_user,
            db_session,
        )
        logger.info("Upload Invoice file. %s", str(invoice))

        return self.serialize_invoice(invoice)
