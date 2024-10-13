"""Asset router"""

from typing import Annotated, List, Union

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi_filter import FilterDepends
from sqlalchemy.orm import Session

from src.asset.filters import (
    AssetFilter,
    AssetSelectFilter,
    AssetStatusFilter,
    AssetTypeFilter,
)
from src.asset.schemas import (
    DisposalAssetSchema,
    InactivateAssetSchema,
    NewAssetSchema,
    UpdateAssetSchema,
)
from src.asset.scripts import fix_asset_status
from src.asset.service import AssetService
from src.auth.models import UserModel
from src.backends import PermissionChecker, get_db_session
from src.config import (
    MAX_PAGINATION_NUMBER,
    NOT_ALLOWED,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    PAGINATION_NUMBER,
)

asset_router = APIRouter(prefix="/assets", tags=["Asset"])

asset_service = AssetService()


@asset_router.post("/")
def post_create_asset_route(
    data: NewAssetSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "asset", "action": "add"})
    ),
):
    """Creates asset route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = asset_service.create_asset(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@asset_router.patch("/{asset_id}/")
def patch_update_asset_route(
    asset_id: int,
    data: UpdateAssetSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "asset", "action": "edit"})
    ),
):
    """Update asset route"""
    if not authenticated_user:
        db_session.close()
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


@asset_router.patch("/inactivate/{asset_id}/")
def patch_inactivate_asset_route(
    asset_id: int,
    data: InactivateAssetSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "asset", "action": "edit"})
    ),
):
    """Update asset route"""
    if not authenticated_user:
        db_session.close()
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


@asset_router.patch("/disposal/{asset_id}/")
async def patch_disposal_asset_route(
    asset_id: int,
    data: DisposalAssetSchema,
    files: Annotated[
        Union[List[UploadFile], None],
        File(description="Anexos da baixa do ativo"),
    ],
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "asset", "action": "edit"})
    ),
):
    """Update asset route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = await asset_service.disposal_asset(
        asset_id, data, files, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@asset_router.put("/{asset_id}/")
def put_update_asset_route():
    """Update asset Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@asset_router.get("/")
def get_list_assets_route(
    asset_filters: AssetFilter = FilterDepends(AssetFilter, by_alias=True),
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
        PermissionChecker({"module": "asset", "model": "asset", "action": "view"})
    ),
):
    """List assets and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    assets = asset_service.get_assets(db_session, asset_filters, "", fields, page, size)
    db_session.close()
    return assets


@asset_router.get("-select/")
def get_select_assets_route(
    asset_filters: AssetSelectFilter = FilterDepends(AssetSelectFilter),
    ids: str = Query(""),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            [
                {"module": "invoice", "model": "invoice", "action": "add"},
                {"module": "invoice", "model": "invoice", "action": "edit"},
                {"module": "lending", "model": "lending", "action": "add"},
                {"module": "lending", "model": "lending", "action": "edit"},
            ]
        )
    ),
):
    """List assets and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    assets = asset_service.get_assets(
        db_session, asset_filters, ids, "id,register_number,imei,type", 1, size
    )
    db_session.close()
    return assets


@asset_router.get("/{asset_id}/")
def get_asset_route(
    asset_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "asset", "action": "view"})
    ),
):
    """Get an asset route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = asset_service.get_asset(asset_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@asset_router.get("/history/{asset_id}/")
def get_asset_history_route(
    asset_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "asset", "action": "view"})
    ),
):
    """Get an asset route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    history = asset_service.get_asset_lending_history(asset_id, db_session)
    db_session.close()
    return JSONResponse(
        content=history,
        status_code=status.HTTP_200_OK,
    )


@asset_router.get("-types/")
def get_list_asset_types_route(
    filter_asset_type: AssetTypeFilter = FilterDepends(AssetTypeFilter),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "asset_type", "action": "view"})
    ),
):
    """List asset types and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    assets_types = asset_service.get_asset_types(db_session, filter_asset_type, fields)
    db_session.close()
    return JSONResponse(content=assets_types, status_code=status.HTTP_200_OK)


@asset_router.get("-status/")
def get_list_asset_status_route(
    filter_asset_status: AssetStatusFilter = FilterDepends(AssetStatusFilter),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "asset", "model": "asset_status", "action": "view"}
        )
    ),
):
    """List asset status and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    assets_status = asset_service.get_asset_status(
        db_session, filter_asset_status, fields
    )
    db_session.close()
    return JSONResponse(content=assets_status, status_code=status.HTTP_200_OK)


@asset_router.get("/disposal-reasons/")
def get_disposal_reasons_route(
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            [
                {"module": "asset", "model": "asset_disposal_reason", "action": "view"},
                {"module": "asset", "model": "asset_disposal_reason", "action": "edit"},
            ]
        )
    ),
):
    """Get disposal reasons route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    disposal_reasons = asset_service.get_disposal_reasons(db_session)
    db_session.close()
    return JSONResponse(content=disposal_reasons, status_code=status.HTTP_200_OK)


@asset_router.post("/bulk-create/")
async def post_create_bulk_upload_file(
    file: Annotated[
        UploadFile,
        File(description="Arquivo CSV ou XSLX com os ativos a serem criados"),
    ],
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "asset", "action": "add"})
    ),
):
    """Bulk create assets from a csv file"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not file.filename.endswith((".csv", ".xlsx")):
        db_session.close()
        return JSONResponse(
            content="Arquivo inválido. Por favor, envie um arquivo CSV ou XLSX.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    response_data = await asset_service.upload_file_to_bulk_create(db_session, file)
    db_session.close()
    if response_data.get("error"):
        return JSONResponse(
            content=response_data, status_code=status.HTTP_400_BAD_REQUEST
        )
    return JSONResponse(content=response_data, status_code=status.HTTP_201_CREATED)


@asset_router.get("/run/fix-status/")
async def get_run_fix_assets_status_route(
    db_session: Session = Depends(get_db_session),
):
    """Run fix assets status route"""
    fix_asset_status(db_session)
    return JSONResponse(content="OK", status_code=status.HTTP_200_OK)
