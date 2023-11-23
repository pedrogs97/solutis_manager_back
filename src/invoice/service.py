"""Invoice service"""
import logging
from typing import List

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.config import MEDIA_UPLOAD_DIR
from src.invoice.models import InvoiceModel
from src.invoice.schemas import (
    InvoiceSerializerSchema,
    NewInvoiceSchema,
    UploadInvoiceSchema,
)
from src.lending.models import AssetModel, AssetTypeModel
from src.lending.schemas import AssetSerializerSchema
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
                detail={"invoice": "Nota fiscal não encontrada"},
            )

        return invoice

    def __validate_nested(
        self, data: NewInvoiceSchema, db_session: Session
    ) -> List[AssetModel]:
        """Validate asstes"""
        assets = []
        if len(data.assets):
            for asset_id in data.assets:
                asset = (
                    db_session.query(AssetModel)
                    .filter(AssetModel.id == asset_id)
                    .first()
                )
                if not asset:
                    raise HTTPException(
                        detail={"assets": f"Ativo não existe. {asset_id}"},
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

                assets.append(asset)
        return assets

    def serialize_invoice(self, invoice: InvoiceModel) -> InvoiceSerializerSchema:
        """Serialize invoice"""
        assets = [AssetSerializerSchema(**asset.__dict__) for asset in invoice.assets]
        return InvoiceSerializerSchema(**invoice.__dict__, assets=[assets])

    def create_invoice(
        self,
        new_invoice: NewInvoiceSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> InvoiceSerializerSchema:
        """Creates new invoice"""

        assets = self.__validate_nested(new_invoice, db_session)

        new_invoice_db = InvoiceModel(**new_invoice.model_dump(by_alias=False))

        new_invoice_db.assets = assets
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

    def get_invoice(
        self, invoice_id: int, db_session: Session
    ) -> InvoiceSerializerSchema:
        """Get a invoice"""
        invoice = self.__get_invoice_or_404(invoice_id, db_session)
        return self.serialize_invoice(invoice)

    def get_invoices(
        self,
        db_session: Session,
        search: str = "",
        filter_invoice: str = None,
        page: int = 1,
        size: int = 50,
    ) -> Page[AssetSerializerSchema]:
        """Get invoices list"""

        invoice_list_query = (
            db_session.query(InvoiceModel)
            .join(
                InvoiceModel.assets,
                AssetTypeModel,
            )
            .filter(
                or_(
                    InvoiceModel.number.ilike(f"%{search}"),
                    AssetModel.code.ilike(f"%{search}%"),
                    AssetModel.description.ilike(f"%{search}%"),
                    AssetModel.register_number.ilike(f"%{search}%"),
                )
            )
        )

        if filter_invoice:
            invoice_list_query = invoice_list_query.filter(
                AssetTypeModel.name == filter_invoice,
            )

        params = Params(page=page, size=size)
        paginated = paginate(
            invoice_list_query,
            params=params,
            transformer=lambda invoice_list_query: [
                self.serialize_invoice(invoice) for invoice in invoice_list_query
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
        file_path = await upload_file(
            file_name, "invoice", invoice_file.file.read(), MEDIA_UPLOAD_DIR
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
