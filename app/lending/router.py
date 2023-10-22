"""Lending router"""
from typing import List, Union, Annotated
from fastapi import APIRouter, status, Depends, Query, Form, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from app.backends import (
    get_db_session,
    PermissionChecker,
)
from app.lending.schemas import (
    AssetTotvsSchema,
    AssetTypeTotvsSchema,
    NewAssetSchema,
    UpdateAssetSchema,
    InactivateAssetSchema,
    CostCenterTotvsSchema,
    NewLendingDocSchema,
    UploadSignedContractSchema,
    NewVerificationSchema,
    NewVerificationAnswerSchema,
)
from app.lending.service import (
    AssetService,
    LendingService,
    DocumentService,
    VerificationService,
)
from app.config import (
    PAGINATION_NUMBER,
    MAX_PAGINATION_NUMBER,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    NOT_ALLOWED,
)
from app.auth.models import UserModel

lending_router = APIRouter(prefix="/lending", tags=["lending"])

asset_service = AssetService()
lending_service = LendingService()
document_service = DocumentService()
verification_service = VerificationService()


@lending_router.post("/assets/update/")
async def post_updates_route(
    data: List[AssetTotvsSchema],
    db_session: Session = Depends(get_db_session),
):
    """Update asset from TOTVS route"""
    asset_service.update_asset_totvs(data, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@lending_router.post("/asset-type/update/")
async def post_asset_type_updates_route(
    data: List[AssetTypeTotvsSchema],
    db_session: Session = Depends(get_db_session),
):
    """Update asset from TOTVSroute"""
    asset_service.update_asset_type_totvs(data, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@lending_router.post("/cost-center/update/")
async def post_cost_center_updates_route(
    data: List[CostCenterTotvsSchema],
    db_session: Session = Depends(get_db_session),
):
    """Update asset from TOTVSroute"""
    asset_service.update_cost_center_totvs(data, db_session)
    return JSONResponse(content="", status_code=status.HTTP_200_OK)


@lending_router.post("/assets/")
async def post_create_asset_route(
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
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@lending_router.patch("/assets/{asset_id}/")
async def patch_update_asset_route(
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
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@lending_router.patch("/assets/inactivate/{asset_id}/")
async def patch_inactivate_asset_route(
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
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@lending_router.put("/assets/{asset_id}/")
async def put_update_asset_route():
    """Update asset Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@lending_router.get("/assets/")
async def get_list_assets_route(
    search: str = "",
    filter_asset: str = None,
    active: bool = True,
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
    return JSONResponse(
        content=asset_service.get_assets(
            db_session, search, filter_asset, active, page, size
        ),
        status_code=status.HTTP_200_OK,
    )


@lending_router.get("/assets/{asset_id}/")
async def get_asset_route(
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
    return JSONResponse(
        content=asset_service.get_asset(asset_id, db_session).model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.post("/documents/create/", response_class=FileResponse)
async def post_create_contract(
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
        new_lending_doc, db_session, authenticated_user
    )

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

    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.post("/verifications/")
async def post_create_verifications(
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

    return JSONResponse(
        content=verification_service.create_verification(
            data, db_session, authenticated_user
        ).model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.get("/verifications/{asset_type_id}/")
async def get_asset_type_verifications(
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
        asset_type_id, db_session, authenticated_user
    )
    return JSONResponse(
        content=[
            serializer.model_dump(by_alias=True) for serializer in list_serializer
        ],
        status_code=status.HTTP_200_OK,
    )


@lending_router.post("/verifications/answer/")
async def post_create_answer_verification(
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

    return JSONResponse(
        content=verification_service.create_verification(
            data, db_session, authenticated_user
        ).model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )
