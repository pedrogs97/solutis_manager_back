"""Lending router"""
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
from src.lending.schemas import (
    InactivateAssetSchema,
    NewAssetSchema,
    NewLendingDocSchema,
    NewLendingSchema,
    NewMaintenanceSchema,
    NewVerificationAnswerSchema,
    NewVerificationSchema,
    UpdateAssetSchema,
    UpdateMaintenanceSchema,
    UploadSignedContractSchema,
)
from src.lending.service import (
    AssetService,
    DocumentService,
    LendingService,
    MaintenanceService,
    VerificationService,
)

lending_router = APIRouter(prefix="/lendings", tags=["Lending"])

asset_service = AssetService()
lending_service = LendingService()
document_service = DocumentService()
verification_service = VerificationService()
maintenance_service = MaintenanceService()


@lending_router.post("/")
def post_create_lending_route(
    data: NewLendingSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "lending", "action": "add"})
    ),
):
    """
    Creates a lending route.

    Args:
        data (NewLendingSchema): The data required to create a lending.
        db_session (Session): The SQLAlchemy database session.
        authenticated_user (Union[UserModel, None]): The authenticated user making the request.

    Returns:
        JSONResponse: The response containing the serialized lending data if the lending was created successfully,
        or a 401 Unauthorized response if the user is not authenticated.
    """
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = lending_service.create_lending(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@lending_router.get("/")
def get_list_lendings_route(
    search: str = "",
    filter_lending: str = None,
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "lending", "action": "view"})
    ),
):
    """List lendings and apply filters route

    Retrieves a list of lendings and applies filters based on the provided parameters.

    Args:
        search (str, optional): A string used for searching lendings. Defaults to "".
        filter_lending (str, optional): A string used for filtering lendings based on asset. Defaults to None.
        page (int, optional): An integer representing the page number of the results. Defaults to 1.
        size (int, optional): An integer representing the number of results per page. Defaults to PAGINATION_NUMBER.
        db_session (Session, optional): The database session. Defaults to Depends(get_db_session).
        authenticated_user (Union[UserModel, None], optional): The authenticated user. Defaults to Depends(PermissionChecker).

    Returns:
        JSONResponse: JSON response containing the retrieved lendings with a status code of 200.
    """
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    assets = lending_service.get_lendings(
        db_session, search, filter_lending, page, size
    )
    db_session.close()
    return JSONResponse(
        content=assets,
        status_code=status.HTTP_200_OK,
    )


@lending_router.get("/{lending_id}/")
def get_lending_route(
    lending_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "lending", "action": "view"})
    ),
):
    """
    Get lending information for a specific lending ID.

    Args:
        lending_id (int): The ID of the lending to retrieve.
        db_session (Session, optional): An instance of the SQLAlchemy Session class for database operations.
            Defaults to Depends(get_db_session).
        authenticated_user (Union[UserModel, None], optional): An instance of the UserModel class or None,
            obtained from the PermissionChecker dependency. Defaults to Depends(PermissionChecker(...)).

    Returns:
        JSONResponse: A JSON response containing the serialized lending information and a status code.
    """
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = lending_service.get_lending(lending_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.post("/assets/")
def post_create_asset_route(
    data: NewAssetSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "asset", "action": "add"})
    ),
):
    """Creates asset route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = asset_service.create_asset(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@lending_router.patch("/assets/{asset_id}/")
def patch_update_asset_route(
    asset_id: int,
    data: UpdateAssetSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "asset", "action": "edit"})
    ),
):
    """Update asset route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = asset_service.update_asset(
        asset_id, data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@lending_router.patch("/assets/inactivate/{asset_id}/")
def patch_inactivate_asset_route(
    asset_id: int,
    data: InactivateAssetSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "asset", "action": "edit"})
    ),
):
    """Update asset route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = asset_service.inactivate_asset(
        asset_id, data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@lending_router.put("/assets/{asset_id}/")
def put_update_asset_route():
    """Update asset Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@lending_router.get("/assets/")
def get_list_assets_route(
    search: str = "",
    filter_asset: str = None,
    active: bool = True,
    fields: str = "",
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "asset", "action": "view"})
    ),
):
    """List assets and apply filters route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    assets = asset_service.get_assets(
        db_session, search, filter_asset, active, fields, page, size
    )
    db_session.close()
    return JSONResponse(
        content=assets,
        status_code=status.HTTP_200_OK,
    )


@lending_router.get("/assets/{asset_id}/")
def get_asset_route(
    asset_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "asset", "action": "view"})
    ),
):
    """Get an asset route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = asset_service.get_asset(asset_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.get("/assets-types/")
def get_list_asset_types_route(
    search: str = "",
    filter_asset_type: str = None,
    fields: str = "",
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "lending", "model": "asset_type", "action": "view"}
        )
    ),
):
    """List asset types and apply filters route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    assets_types = asset_service.get_asset_types(
        db_session, search, filter_asset_type, fields, page, size
    )
    db_session.close()
    return JSONResponse(
        content=assets_types,
        status_code=status.HTTP_200_OK,
    )


@lending_router.get("/assets-status/")
def get_list_asset_status_route(
    filter_asset_status: str = None,
    fields: str = "",
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "lending", "model": "asset_status", "action": "view"}
        )
    ),
):
    """List asset status and apply filters route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    assets_status = asset_service.get_asset_status(
        db_session, filter_asset_status, fields, page, size
    )
    db_session.close()
    return JSONResponse(
        content=assets_status,
        status_code=status.HTTP_200_OK,
    )


@lending_router.post("/contracts/create/", response_class=FileResponse)
def post_create_contract(
    new_lending_doc: Annotated[NewLendingDocSchema, Form()],
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
        new_lending_doc, "Contrato de Comodato", db_session, authenticated_user
    )

    db_session.close()
    return FileResponse(new_doc.path)


@lending_router.post("/contracts/revoke/", response_class=FileResponse)
def post_revoke_contract(
    new_lending_doc: Annotated[NewLendingDocSchema, Form()],
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

    new_doc = document_service.create_contract(
        new_lending_doc, "Distrato de Comodato", db_session, authenticated_user
    )

    db_session.close()
    return FileResponse(new_doc.path)


@lending_router.post("/terms/create/", response_class=FileResponse)
def post_create_term(
    new_lending_doc: Annotated[NewLendingDocSchema, Form()],
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

    new_doc = document_service.create_contract(
        new_lending_doc, "Contrato de Comodato", db_session, authenticated_user
    )

    db_session.close()
    return FileResponse(new_doc.path)


@lending_router.post("/terms/revoke/", response_class=FileResponse)
def post_revoke_term(
    new_lending_doc: Annotated[NewLendingDocSchema, Form()],
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

    new_doc = document_service.create_contract(
        new_lending_doc, "Distrato de Comodato", db_session, authenticated_user
    )

    db_session.close()
    return FileResponse(new_doc.path)


@lending_router.post("/documents/upload/")
async def post_import_contract(
    data: Annotated[UploadSignedContractSchema, Form()],
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
        file, data, db_session, authenticated_user
    )

    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.post("/verifications/")
def post_create_verifications(
    data: NewVerificationSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "lending", "model": "verification", "action": "add"}
        )
    ),
):
    """Creates new verification"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = verification_service.create_verification(
        data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.get("/verifications/{asset_type_id}/")
def get_asset_type_verifications(
    asset_type_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "lending", "model": "verification", "action": "view"}
        )
    ),
):
    """Get asset type verifications"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    list_serializer = verification_service.get_asset_verifications(
        asset_type_id, db_session
    )
    db_session.close()
    return JSONResponse(
        content=[
            serializer.model_dump(by_alias=True) for serializer in list_serializer
        ],
        status_code=status.HTTP_200_OK,
    )


@lending_router.post("/verifications/answer/")
def post_create_answer_verification(
    data: NewVerificationAnswerSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "answer", "action": "add"})
    ),
):
    """Creates answer for a verification"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = verification_service.create_verification(
        data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.post("/maintenances/")
def post_create_maintenance_route(
    data: NewMaintenanceSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "lending", "model": "maintenance", "action": "add"}
        )
    ),
):
    """Creates maintenance route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = maintenance_service.create_maintenance(
        data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@lending_router.patch("/maintenances/{maintenance_id}/")
def patch_update_maintenance_route(
    maintenance_id: int,
    data: UpdateMaintenanceSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "lending", "model": "maintenance", "action": "edit"}
        )
    ),
):
    """Update maintenance route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = maintenance_service.update_maintenance(
        data, maintenance_id, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@lending_router.put("/maintenances/{maintenance_id}/")
def put_update_maintenance_route():
    """Update maintenance Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@lending_router.get("/maintenances/")
def get_list_maintenances_route(
    search: str = "",
    filter_maintenance: str = None,
    inital_date: str = None,
    final_date: str = None,
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "lending", "model": "maintenance", "action": "view"}
        )
    ),
):
    """List maintenances and apply filters route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    maintenances = maintenance_service.get_maintenances(
        db_session, search, filter_maintenance, inital_date, final_date, page, size
    )
    db_session.close()
    return JSONResponse(
        content=maintenances,
        status_code=status.HTTP_200_OK,
    )


@lending_router.get("/maintenances/{maintenance_id}/")
def get_maintenance_route(
    maintenance_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "lending", "model": "maintenance", "action": "view"}
        )
    ),
):
    """Get an maintenance route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = maintenance_service.get_maintenance(maintenance_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )
