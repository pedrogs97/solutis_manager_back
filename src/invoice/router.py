"""Invoice router"""
from typing import Annotated, Union

from fastapi import APIRouter, Depends, Form, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.backends import PermissionChecker, get_db_session
from src.config import (
    MAX_PAGINATION_NUMBER,
    NOT_ALLOWED,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    PAGINATION_NUMBER,
)
from src.invoice.schemas import NewInvoiceSchema, UploadInvoiceSchema
from src.invoice.service import InvoiceService

invoice_service = InvoiceService()
invoice_router = APIRouter(prefix="/invoice", tags=["invoice"])


@invoice_router.post("/invoices/")
def post_create_invoice_route(
    data: NewInvoiceSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "invoice", "model": "invoice", "action": "add"})
    ),
):
    """Creates invoice route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = invoice_service.create_invoice(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@invoice_router.patch("/invoices/{invoice_id}/")
def patch_update_invoice_route():
    """Update invoice Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@invoice_router.put("/invoices/{invoice_id}/")
def put_update_invoice_route():
    """Update invoice Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@invoice_router.get("/invoices/")
def get_list_invoices_route(
    search: str = "",
    filter_invoice: str = None,
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "invoice", "model": "invoice", "action": "view"})
    ),
):
    """List invoices and apply filters route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    invoices = invoice_service.get_invoices(
        db_session, search, filter_invoice, page, size
    )
    db_session.close()
    return JSONResponse(
        content=invoices,
        status_code=status.HTTP_200_OK,
    )


@invoice_router.get("/invoices/{invoice_id}/")
def get_invoice_route(
    invoice_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "invoice", "model": "invoice", "action": "view"})
    ),
):
    """Get an invoice route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = invoice_service.get_invoice(invoice_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@invoice_router.post("/invoices/file/", response_class=FileResponse)
async def post_import_invoice_file(
    new_invoice_doc: Annotated[UploadInvoiceSchema, Form()],
    file: UploadFile,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "invoice", "model": "invoice", "action": "add"})
    ),
):
    """Import a new invoice file"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    serializer = await invoice_service.upload_invoice(
        file, new_invoice_doc, db_session, authenticated_user
    )

    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )
