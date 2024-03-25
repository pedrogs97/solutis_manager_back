"""Maintenance router"""

from typing import Annotated, List, Union

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
from src.maintenance.filters import MaintenanceFilter, UpgradeFilter
from src.maintenance.schemas import (
    NewMaintenanceSchema,
    NewUpgradeSchema,
    UpdateMaintenanceSchema,
    UpdateUpgradeSchema,
)
from src.maintenance.service import MaintenanceService, UpgradeService

maintenance_router = APIRouter(prefix="/maintenances", tags=["Maintenance"])

maintenance_service = MaintenanceService()
upgrade_service = UpgradeService()


@maintenance_router.post("/")
def post_create_maintenance_route(
    data: NewMaintenanceSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "add"})
    ),
):
    """Creates maintenance route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = maintenance_service.create_maintenance(
        data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@maintenance_router.patch("/{maintenance_id}/")
def patch_update_maintenance_route(
    maintenance_id: int,
    data: UpdateMaintenanceSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "edit"})
    ),
):
    """Update maintenance route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = maintenance_service.update_maintenance(
        data, maintenance_id, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@maintenance_router.put("/{maintenance_id}/")
def put_update_maintenance_route():
    """Update maintenance Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@maintenance_router.get("/")
def get_list_maintenances_route(
    maintenance_filters: MaintenanceFilter = FilterDepends(MaintenanceFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "view"})
    ),
):
    """List maintenances and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    maintenances = maintenance_service.get_maintenances(
        db_session, maintenance_filters, page, size
    )
    db_session.close()
    return maintenances


@maintenance_router.get("/{maintenance_id}/")
def get_maintenance_route(
    maintenance_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "view"})
    ),
):
    """Get a maintenance route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = maintenance_service.get_maintenance(maintenance_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@maintenance_router.post("/upload/maintenance/")
async def post_upload_maintenance_attachments(
    files: List[UploadFile],
    maintenanceId: Annotated[int, Form()],
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "edit"})
    ),
):
    """Upload attachmetns route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer_list = await maintenance_service.upload_attachments(
        files, maintenanceId, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=[
            serializer.model_dump(by_alias=True) for serializer in serializer_list
        ],
        status_code=status.HTTP_200_OK,
    )


@maintenance_router.get(
    "/attachments/download/{attachment_id}/", response_class=FileResponse
)
def get_download_attachment_maintenance(
    attachment_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "view"})
    ),
):
    """Download a attachment maintenance"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)

    attach = maintenance_service.get_attachment(
        attachment_id,
        db_session,
    )

    db_session.close()

    headers = {"Access-Control-Expose-Headers": "Content-Disposition"}
    return FileResponse(attach.path, filename=attach.file_name, headers=headers)


@maintenance_router.get("-actions/")
def get_list_maintenances_actions_route(
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "view"})
    ),
):
    """List maintenances actions route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    actions = maintenance_service.get_maintenance_actions(db_session)
    db_session.close()
    return actions


@maintenance_router.get("-status/")
def get_list_maintenances_status_route(
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "view"})
    ),
):
    """List maintenances status route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    maintenances_status = maintenance_service.get_maintenance_status(db_session)
    db_session.close()
    return maintenances_status


@maintenance_router.post("-upgrade/")
def post_create_upgrade_route(
    data: NewUpgradeSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "add"})
    ),
):
    """Creates upgrade route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = upgrade_service.create_upgrade(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@maintenance_router.patch("-upgrade/{upgrade_id}/")
def patch_update_upgrade_route(
    upgrade_id: int,
    data: UpdateUpgradeSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "edit"})
    ),
):
    """Update upgrade route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = upgrade_service.update_upgrade(
        data, upgrade_id, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@maintenance_router.put("-upgrade/{upgrade_id}/")
def put_update_upgrade_route():
    """Update upgrade Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@maintenance_router.get("-upgrade/")
def get_list_upgrades_route(
    upgrade_filters: UpgradeFilter = FilterDepends(UpgradeFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "view"})
    ),
):
    """List upgrades and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    upgrades = upgrade_service.get_upgrades(db_session, upgrade_filters, page, size)
    db_session.close()
    return upgrades


@maintenance_router.get("-upgrade/{maintenance_id}/")
def get_upgrade_route(
    maintenance_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "view"})
    ),
):
    """Get an upgrade route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = upgrade_service.get_upgrade(maintenance_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@maintenance_router.post("/upload/upgrade/")
async def post_upload_upgrade_attachments(
    files: List[UploadFile],
    upgradeId: Annotated[int, Form()],
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "edit"})
    ),
):
    """Upload attachmetns route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer_list = await upgrade_service.upload_attachments(
        files, upgradeId, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=[
            serializer.model_dump(by_alias=True) for serializer in serializer_list
        ],
        status_code=status.HTTP_200_OK,
    )


@maintenance_router.get(
    "-upgrade/attachments/download/{attachment_id}/", response_class=FileResponse
)
def get_download_attachment_upgrade(
    attachment_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "view"})
    ),
):
    """Download a attachment upgrade"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)

    attach = upgrade_service.get_attachment(
        attachment_id,
        db_session,
    )

    db_session.close()

    headers = {"Access-Control-Expose-Headers": "Content-Disposition"}
    return FileResponse(attach.path, filename=attach.file_name, headers=headers)
