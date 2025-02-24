"""Report router"""

from typing import Union

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi_filter import FilterDepends
from sqlalchemy.orm import Session

from src.asset.models import AssetModel
from src.auth.models import UserModel
from src.backends import PermissionChecker, get_db_session
from src.config import (
    MAX_PAGINATION_NUMBER,
    NOT_ALLOWED,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    PAGINATION_NUMBER,
)
from src.lending.models import LendingModel
from src.report.filters import (
    AssetPatternFilter,
    AssetReportFilter,
    AssetStockReportFilter,
    LendingReportFilter,
    MaintenanceReportFilter,
)
from src.report.service import ReportService
from src.report.service import get_dashboard as get_dashboard_service

report_router = APIRouter(prefix="/report", tags=["Report"])

REPORT_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@report_router.get("/list/by-employee/")
def get_list_report_by_employee_route(
    report_filters: LendingReportFilter = FilterDepends(LendingReportFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
) -> JSONResponse:
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService()
    report_list = report_service.report_list_by_employee(
        report_filters, db_session, page, size
    )
    db_session.close()
    return report_list


@report_router.get("/by-employee/")
def get_report_by_employee_route(
    db_session: Session = Depends(get_db_session),
    report_filters: LendingReportFilter = FilterDepends(LendingReportFilter),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService()
    file = report_service.report_by_employee(
        report_filters,
        db_session,
    )

    if not file:
        db_session.close()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    db_session.close()
    headers = {
        "Access-Control-Expose-Headers": "Content-Disposition",
        "Content-Disposition": f'attachment; filename="{report_service.REPORT_FILE_NAME}"',
    }
    return StreamingResponse(
        content=file,
        headers=headers,
        media_type=REPORT_MEDIA_TYPE,
    )


@report_router.get("/list/by-asset/")
def get_list_report_by_asset_route(
    report_filters: AssetReportFilter = FilterDepends(AssetReportFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
) -> JSONResponse:
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService()
    report_list = report_service.report_list_by_asset(
        report_filters, db_session, page, size
    )
    db_session.close()
    return report_list


@report_router.get("/by-asset/")
def get_report_by_asset_route(
    db_session: Session = Depends(get_db_session),
    report_filters: AssetReportFilter = FilterDepends(AssetReportFilter),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService("CONSULTA POR EQUIPAMENTO")
    file = report_service.report_by_asset(
        report_filters,
        db_session,
    )

    if not file:
        db_session.close()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    db_session.close()
    headers = {
        "Access-Control-Expose-Headers": "Content-Disposition",
        "Content-Disposition": f'attachment; filename="{report_service.REPORT_FILE_NAME}"',
    }
    return StreamingResponse(
        content=file,
        headers=headers,
        media_type=REPORT_MEDIA_TYPE,
    )


@report_router.get("/list/by-pattern/")
def get_list_report_by_pattern_route(
    report_filters: AssetPatternFilter = FilterDepends(AssetPatternFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
) -> JSONResponse:
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService()
    report_list = report_service.report_list_by_asset_pattern(
        report_filters, db_session, page, size
    )
    db_session.close()
    return report_list


@report_router.get("/by-pattern/")
def get_report_by_pattern_route(
    db_session: Session = Depends(get_db_session),
    report_filters: AssetPatternFilter = FilterDepends(AssetPatternFilter),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService("CONSULTA PADRÃO DE EQUIPAMENTO")
    file = report_service.report_by_asset_pattern(
        report_filters,
        db_session,
    )

    if not file:
        db_session.close()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    db_session.close()
    headers = {
        "Access-Control-Expose-Headers": "Content-Disposition",
        "Content-Disposition": f'attachment; filename="{report_service.REPORT_FILE_NAME}"',
    }
    return StreamingResponse(
        content=file,
        headers=headers,
        media_type=REPORT_MEDIA_TYPE,
    )


@report_router.get("/by-maintenance/")
def get_report_by_maintenance_route(
    db_session: Session = Depends(get_db_session),
    report_filters: MaintenanceReportFilter = FilterDepends(MaintenanceReportFilter),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService("CONSULTA POR MANUTENÇÃO")
    file = report_service.report_by_maintenance(report_filters, db_session)

    if not file:
        db_session.close()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    db_session.close()
    headers = {
        "Access-Control-Expose-Headers": "Content-Disposition",
        "Content-Disposition": f'attachment; filename="{report_service.REPORT_FILE_NAME}"',
    }
    return StreamingResponse(
        content=file,
        headers=headers,
        media_type=REPORT_MEDIA_TYPE,
    )


@report_router.get("/list/by-maintenance/")
def get_list_report_by_maintenance_route(
    db_session: Session = Depends(get_db_session),
    report_filters: MaintenanceReportFilter = FilterDepends(MaintenanceReportFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
) -> JSONResponse:
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService()
    report_list = report_service.report_list_by_maintenance(
        report_filters, db_session, page, size
    )
    db_session.close()
    return report_list


@report_router.get("/list/by-asset-stock/")
def get_list_report_by_asset_stock_route(
    report_filters: AssetStockReportFilter = FilterDepends(AssetStockReportFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
) -> JSONResponse:
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService()
    report_list = report_service.report_list_by_asset_stock(
        report_filters, db_session, page, size
    )
    db_session.close()
    return report_list


@report_router.get("/by-asset-stock/")
def get_report_by_asset_stock_route(
    db_session: Session = Depends(get_db_session),
    report_filters: AssetStockReportFilter = FilterDepends(AssetStockReportFilter),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Login user route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    report_service = ReportService("RELATÓRIO DE ESTOQUE DE ATIVOS")
    file = report_service.report_by_asset_stock(
        report_filters,
        db_session,
    )

    if not file:
        db_session.close()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    db_session.close()
    headers = {
        "Access-Control-Expose-Headers": "Content-Disposition",
        "Content-Disposition": f'attachment; filename="{report_service.REPORT_FILE_NAME}"',
    }
    return StreamingResponse(
        content=file,
        headers=headers,
        media_type=REPORT_MEDIA_TYPE,
    )


@report_router.get("/projects-select/")
def get_projects(
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Projects select route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    unique_projects = (
        db_session.query(LendingModel.business_executive)
        .filter(LendingModel.deleted.is_(False))
        .distinct()
    )

    db_session.close()
    return JSONResponse(
        content=[
            {
                "label": unique_tuple[0],
                "value": unique_tuple[0],
            }
            for unique_tuple in unique_projects
        ],
        status_code=status.HTTP_200_OK,
    )


@report_router.get("/business-executive-select/")
def get_business_executives(
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Business executive select route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    unique_business_executives = (
        db_session.query(LendingModel.business_executive)
        .filter(LendingModel.deleted.is_(False))
        .distinct()
    )

    db_session.close()
    return JSONResponse(
        content=[
            {
                "label": unique_tuple[0],
                "value": unique_tuple[0],
            }
            for unique_tuple in unique_business_executives
        ],
        status_code=status.HTTP_200_OK,
    )


@report_router.get("/pattern-select/")
def get_pattern(
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Pattern select route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    unique_patterns = filter(
        lambda item: item[0] != "" and item[0] is not None,
        db_session.query(AssetModel.pattern).distinct(),
    )

    db_session.close()
    return JSONResponse(
        content=[
            {
                "label": unique_tuple[0],
                "value": unique_tuple[0],
            }
            for unique_tuple in unique_patterns
        ],
        status_code=status.HTTP_200_OK,
    )


@report_router.get("/asset-pdf/{asset_id}/")
def get_asset_pdf(
    asset_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Asset PDF route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    report_service = ReportService("CONSULTA POR EQUIPAMENTO")
    file_path, filename = report_service.report_asset_timeline(asset_id, db_session)

    db_session.close()
    headers = {
        "Access-Control-Expose-Headers": "Content-Disposition",
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    return FileResponse(
        file_path,
        filename=filename,
        headers=headers,
        media_type="application/pdf; charset=utf-8",
    )


@report_router.get("/dashboard/")
def get_dashboard(
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "report", "model": "report", "action": "view"})
    ),
):
    """Dashboard route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    dashboard = get_dashboard_service(db_session)

    db_session.close()
    return JSONResponse(
        content=dashboard,
        status_code=status.HTTP_200_OK,
    )
