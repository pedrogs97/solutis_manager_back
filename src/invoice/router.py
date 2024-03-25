"""Invoice router"""

from typing import Annotated, Union

from fastapi import APIRouter, Depends, Form, Query, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi_filter import FilterDepends
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
from src.invoice.filters import InvoiceFilter
from src.invoice.schemas import NewInvoiceSchema
from src.invoice.service import InvoiceService

invoice_service = InvoiceService()
invoice_router = APIRouter(prefix="/invoice", tags=["Invoice"])


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
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)

    serializer = invoice_service.create_invoice(
        data,
        db_session,
        authenticated_user,
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@invoice_router.post("/invoices/document/upload")
async def post_upload_document_invoice_route(
    invoice: Annotated[int, Form()],
    invoice_file: UploadFile,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "invoice", "model": "invoice", "action": "edit"})
    ),
):
    """Upload document invoice route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)

    serializer = await invoice_service.upload_document_invoice(
        invoice,
        invoice_file,
        db_session,
        authenticated_user,
    )
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
    invoice_filters: InvoiceFilter = FilterDepends(InvoiceFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    deleted: int = Query(0, description="Filter deleted"),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "invoice", "model": "invoice", "action": "view"})
    ),
):
    """List invoices and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    invoices = invoice_service.get_invoices(
        db_session, invoice_filters, page, size, deleted
    )
    db_session.close()
    return invoices


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
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = invoice_service.get_invoice(invoice_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@invoice_router.delete("/invoices/{invoice_id}/")
def delete_invoice_route(
    invoice_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "invoice", "model": "invoice", "action": "delete"})
    ),
):
    """Delete an invoice route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = invoice_service.delete_invoice(invoice_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )
