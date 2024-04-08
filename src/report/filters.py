"""Report filters"""

from typing import List, Optional, Union

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import Select
from sqlalchemy.orm import Query
from sqlalchemy.sql.expression import and_, or_

from src.asset.models import AssetModel, AssetStatusModel
from src.lending.models import LendingModel, WorkloadModel
from src.log.models import LogModel
from src.people.models import EmployeeModel


class LendingReportFilter(Filter):
    """Lending report filter"""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    employees_ids: Optional[str] = None
    roles_ids: Optional[str] = None
    projects: Optional[str] = None
    business_executive: Optional[str] = None
    workloads_ids: Optional[str] = None
    register_number: Optional[str] = None
    patterns: Optional[str] = None
    assets_status_ids: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = LendingModel

    def filter(
        self, query_lending: Union[Query, Select], query_log: Union[Query, Select]
    ) -> Query:
        """Filter query"""
        previous_lending: List[LogModel] = query_log.filter(
            LogModel.model == "Lending",
            LogModel.operation.startswith("Criação"),
            LogModel.logged_in.between(self.start_date, self.end_date),
        ).all()
        employees_ids_list = (
            self.employees_ids.split(",")
            if self.employees_ids.index(",")
            else [self.employees_ids]
        )
        roles_ids_list = (
            self.roles_ids.split(",") if self.roles_ids.index(",") else [self.roles_ids]
        )
        projects_list = (
            self.projects.split(",") if self.projects.index(",") else [self.projects]
        )
        business_executive_list = (
            self.business_executive.split(",")
            if self.business_executive.index(",")
            else [self.business_executive]
        )
        workloads_ids_list = (
            self.workloads_ids.split(",")
            if self.workloads_ids.index(",")
            else [self.workloads_ids]
        )
        register_number_list = (
            self.register_number.split(",")
            if self.register_number.index(",")
            else [self.register_number]
        )
        patterns_list = (
            self.patterns.split(",") if self.patterns.index(",") else [self.patterns]
        )
        asset_status_ids_list = (
            self.assets_status_ids.split(",")
            if self.assets_status_ids.index(",")
            else [self.assets_status_ids]
        )
        report_data = (
            query_lending.join(AssetModel, LendingModel.asset_id == AssetModel.id)
            .join(AssetStatusModel)
            .join(EmployeeModel, LendingModel.employee_id == EmployeeModel.id)
            .join(WorkloadModel)
            .filter(
                LendingModel.deleted.is_(False),
                or_(
                    LendingModel.id.in_([lending.id for lending in previous_lending]),
                    and_(
                        LendingModel.employee_id.in_(employees_ids_list),
                        LendingModel.created_at.between(self.start_date, self.end_date),
                        EmployeeModel.role.in_(roles_ids_list),
                        LendingModel.project.in_(projects_list),
                        LendingModel.business_executive.in_(business_executive_list),
                        WorkloadModel.id.in_(workloads_ids_list),
                        AssetModel.register_number.in_(register_number_list),
                        AssetModel.pattern.in_(patterns_list),
                        AssetModel.status.in_(asset_status_ids_list),
                    ),
                ),
            )
        )
        return report_data
