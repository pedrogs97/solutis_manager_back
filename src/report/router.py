"""Report router"""

from typing import List

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.backends import get_db_session
from src.people.models import EmployeeModel
from src.report.service import ReportService

report_router = APIRouter(prefix="/report", tags=["Report"])


@report_router.get("/by-employee/")
def get_report_by_employee_route(
    db_session: Session = Depends(get_db_session),
    start_date: str = Query("", description="Start date"),
    end_date: str = Query("", description="End date"),
    employees_ids: List[int] = Query([], description="Employees Ids"),
):
    """Login user route"""
    report_service = ReportService()
    employees = (
        db_session.query(EmployeeModel)
        .filter(EmployeeModel.id.in_(employees_ids))
        .all()
    )
    report_service.report_by_employee(
        start_date,
        end_date,
        employees,
        db_session,
    )
    db_session.close()
    return JSONResponse(content="ok", status_code=status.HTTP_200_OK)
