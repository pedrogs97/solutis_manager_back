"""Lending router"""

from typing import Annotated, Union

from fastapi import APIRouter, Depends, Form, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
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
from src.document.filters import DocumentFilter
from src.document.schemas import NewLendingDocSchema, NewRevokeContractDocSchema
from src.document.service import DocumentService

document_router = APIRouter(prefix="/documents", tags=["Document"])

document_service = DocumentService()


@document_router.post("/contracts/create/", response_class=FileResponse)
def post_create_contract(
    new_document_doc: NewLendingDocSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "add"})
    ),
):
    """Creates a new contract"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    new_doc = document_service.create_contract(
        new_document_doc, "Contrato de Comodato", db_session, authenticated_user
    )

    db_session.close()

    headers = {"Access-Control-Expose-Headers": "Content-Disposition"}
    return FileResponse(new_doc.path, filename=new_doc.file_name, headers=headers)


@document_router.post("/contracts/upload/")
async def post_import_contract(
    documentId: Annotated[int, Form()],
    file: UploadFile,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "edit"})
    ),
):
    """Upload new contract"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    serializer = await document_service.upload_contract(
        file, "Contrato de Comodato", documentId, db_session, authenticated_user
    )

    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@document_router.post("/contracts/revoke/create/", response_class=FileResponse)
def post_create_revoke_contract(
    data: NewRevokeContractDocSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "add"})
    ),
):
    """Creates a new revoke contract"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    new_doc = document_service.create_revoke_contract(
        data, "Distrato de Comodato", db_session, authenticated_user
    )

    db_session.close()

    headers = {"Access-Control-Expose-Headers": "Content-Disposition"}
    return FileResponse(new_doc.path, filename=new_doc.file_name, headers=headers)


@document_router.post("/contracts/revoke/upload/")
async def post_revoke_contract(
    documentId: Annotated[int, Form()],
    file: UploadFile,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "add"})
    ),
):
    """Creates a new revoke contract"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    serializer = await document_service.upload_revoke_contract(
        file, "Distrato de Comodato", documentId, db_session, authenticated_user
    )

    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@document_router.post("/terms/create/", response_class=FileResponse)
def post_create_term(
    new_document_doc: NewLendingDocSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "add"})
    ),
):
    """Creates a new term"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    new_doc = document_service.create_term(
        new_document_doc, "Termo de Responsabilidade", db_session, authenticated_user
    )

    db_session.close()

    headers = {"Access-Control-Expose-Headers": "Content-Disposition"}
    return FileResponse(new_doc.path, filename=new_doc.file_name, headers=headers)


@document_router.post("/terms/upload/")
async def post_import_term(
    documentId: Annotated[int, Form()],
    file: UploadFile,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "edit"})
    ),
):
    """Upload new term"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    serializer = await document_service.upload_contract(
        file, "Termo de Responsabilidade", documentId, db_session, authenticated_user
    )

    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@document_router.post("/terms/revoke/create/", response_class=FileResponse)
def post_create_revoke_term(
    new_document_doc: NewRevokeContractDocSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "add"})
    ),
):
    """Creates a new term"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    new_doc = document_service.create_revoke_term(
        new_document_doc,
        "Distrato de Termo de Responsabilidade",
        db_session,
        authenticated_user,
    )

    db_session.close()

    headers = {"Access-Control-Expose-Headers": "Content-Disposition"}
    return FileResponse(new_doc.path, filename=new_doc.file_name, headers=headers)


@document_router.post("/terms/revoke/upload/")
async def post_revoke_term(
    documentId: Annotated[int, Form()],
    file: UploadFile,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "add"})
    ),
):
    """Creates a new revoke term"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    serializer = await document_service.upload_revoke_contract(
        file,
        "Distrato de Termo de Responsabilidade",
        documentId,
        db_session,
        authenticated_user,
    )

    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@document_router.get("/list/")
def get_list_documents_route(
    document_filters: DocumentFilter = FilterDepends(DocumentFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "view"})
    ),
):
    """List documents and apply filters route

    Retrieves a list of documents and applies filters based on the provided parameters.

    Args:
        search (str, optional): A string used for searching documents. Defaults to "".
        document_filters (str, optional): A string used for filtering documents based on asset. Defaults to None.
        page (int, optional): An integer representing the page number of the results. Defaults to 1.
        size (int, optional): An integer representing the number of results per page. Defaults to PAGINATION_NUMBER.
        db_session (Session, optional): The database session. Defaults to Depends(get_db_session).
        authenticated_user (Union[UserModel, None], optional): The authenticated user. Defaults to Depends(PermissionChecker).

    Returns:
        JSONResponse: JSON response containing the retrieved documents with a status code of 200.
    """
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    documents = document_service.get_documents(db_session, document_filters, page, size)
    db_session.close()
    return documents


@document_router.get("/download/{document_id}/", response_class=FileResponse)
def get_download_document(
    document_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "document", "action": "view"})
    ),
):
    """Download a document"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    document = document_service.get_document(
        document_id,
        db_session,
    )

    db_session.close()

    headers = {"Access-Control-Expose-Headers": "Content-Disposition"}
    return FileResponse(document.path, filename=document.file_name, headers=headers)
