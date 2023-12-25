"""Maintenance router"""
from typing import Union

from fastapi import APIRouter, Depends, Query, status
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
from src.maintenance.filters import MaintenanceFilter
from src.maintenance.schemas import NewMaintenanceSchema, UpdateMaintenanceSchema
from src.maintenance.service import MaintenanceService

maintenance_router = APIRouter(prefix="/maintenances", tags=["Maintenance"])

maintenance_service = MaintenanceService()


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
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    maintenances = maintenance_service.get_maintenances(
        db_session, maintenance_filters, page, size
    )
    db_session.close()
    return JSONResponse(
        content=maintenances,
        status_code=status.HTTP_200_OK,
    )


@maintenance_router.get("/{maintenance_id}/")
def get_maintenance_route(
    maintenance_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "maintenance", "action": "view"})
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
