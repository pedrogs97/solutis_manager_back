"""Report filters"""

from typing import List, Optional, Union

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import Select
from sqlalchemy.orm import Query
from sqlalchemy.sql.expression import or_

from src.asset.models import AssetModel
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

        query = (
            query_lending.join(AssetModel)
            .join(EmployeeModel)
            .join(WorkloadModel)
            .filter(
                LendingModel.deleted.is_(False),
                or_(
                    LendingModel.id.in_([lending.id for lending in previous_lending]),
                ),
            )
        )

        if self.employees_ids:
            employees_ids_list = (
                self.employees_ids.split(",")
                if self.employees_ids.index(",")
                else [self.employees_ids]
            )
            query = query.filter(EmployeeModel.id.in_(employees_ids_list))

        if self.roles_ids:
            roles_ids_list = (
                self.roles_ids.split(",")
                if self.roles_ids.index(",")
                else [self.roles_ids]
            )
            query = query.filter(EmployeeModel.role.in_(roles_ids_list))

        if self.projects:
            projects_list = (
                self.projects.split(",")
                if self.projects.index(",")
                else [self.projects]
            )
            query = query.filter(LendingModel.project.in_(projects_list))

        if self.business_executive:
            business_executive_list = (
                self.business_executive.split(",")
                if self.business_executive.index(",")
                else [self.business_executive]
            )
            query = query.filter(
                LendingModel.business_executive.in_(business_executive_list)
            )

        if self.workloads_ids:
            workloads_ids_list = (
                self.workloads_ids.split(",")
                if self.workloads_ids.index(",")
                else [self.workloads_ids]
            )
            query = query.filter(WorkloadModel.id.in_(workloads_ids_list))

        if self.register_number:
            register_number_list = (
                self.register_number.split(",")
                if self.register_number.index(",")
                else [self.register_number]
            )
            query = query.filter(AssetModel.register_number.in_(register_number_list))

        if self.patterns:
            patterns_list = (
                self.patterns.split(",")
                if self.patterns.index(",")
                else [self.patterns]
            )
            query = query.filter(AssetModel.pattern.in_(patterns_list))

        if self.assets_status_ids:
            asset_status_ids_list = (
                self.assets_status_ids.split(",")
                if self.assets_status_ids.index(",")
                else [self.assets_status_ids]
            )
            query = query.filter(AssetModel.status.in_(asset_status_ids_list))

        return query
