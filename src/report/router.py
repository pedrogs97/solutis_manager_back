"""Report router"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi_filter import FilterDepends
from sqlalchemy.orm import Session

from src.asset.models import AssetModel
from src.backends import get_db_session
from src.lending.models import LendingModel
from src.report.filters import LendingReportFilter
from src.report.service import ReportService

report_router = APIRouter(prefix="/report", tags=["Report"])


@report_router.get("/by-employee/")
def get_report_by_employee_route(
    db_session: Session = Depends(get_db_session),
    report_filters: LendingReportFilter = FilterDepends(LendingReportFilter),
):
    """Login user route"""
    report_service = ReportService()
    file = report_service.report_by_employee(
        report_filters,
        db_session,
    )
    db_session.close()
    headers = {"Access-Control-Expose-Headers": "Content-Disposition"}
    return FileResponse(file.path, filename=file.file_name, headers=headers)


@report_router.get("/projects-select/")
def get_projects(
    db_session: Session = Depends(get_db_session),
):
    """Projects select route"""
    lendings_project = (
        db_session.query(LendingModel)
        .filter(LendingModel.deleted.is_(False))
        .group_by(LendingModel.project)
        .distinct()
        .all()
    )
    db_session.close()
    return JSONResponse(
        content=[
            {"label": lending_project.project, "value": lending_project.project}
            for lending_project in lendings_project
        ],
        status_code=status.HTTP_200_OK,
    )


@report_router.get("/business-executive-select/")
def get_business_executives(
    db_session: Session = Depends(get_db_session),
):
    """Business executive select route"""
    lendings_business = (
        db_session.query(LendingModel)
        .filter(LendingModel.deleted.is_(False))
        .group_by(LendingModel.business_executive)
        .distinct()
        .all()
    )
    db_session.close()
    return JSONResponse(
        content=[
            {
                "label": lending_business.business_executive,
                "value": lending_business.business_executive,
            }
            for lending_business in lendings_business
        ],
        status_code=status.HTTP_200_OK,
    )


@report_router.get("/pattern-select/")
def get_pattern(
    db_session: Session = Depends(get_db_session),
):
    """Pattern select route"""
    lendings_pattern = (
        db_session.query(LendingModel)
        .join(AssetModel, LendingModel.asset_id == AssetModel.id)
        .filter(LendingModel.deleted.is_(False))
        .group_by(AssetModel.pattern)
        .distinct()
        .all()
    )
    db_session.close()
    return JSONResponse(
        content=[
            {
                "label": lending_pattern.asset.pattern,
                "value": lending_pattern.asset.pattern,
            }
            for lending_pattern in lendings_pattern
        ],
        status_code=status.HTTP_200_OK,
    )
