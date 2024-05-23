"""Report filters"""

from typing import List, Optional, Union

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import Select
from sqlalchemy.orm import Query
from sqlalchemy.sql.expression import or_

from src.asset.models import AssetModel
from src.datasync.models import CostCenterTOTVSModel
from src.lending.models import LendingModel, LendingStatusModel, WorkloadModel
from src.log.models import LogModel
from src.people.models import EmployeeModel


class LendingReportFilter(Filter):
    """Lending report filter"""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    employees_ids: Optional[str] = None
    roles_ids: Optional[str] = None
    bus: Optional[str] = None
    projects: Optional[str] = None
    business_executive: Optional[str] = None
    workloads_ids: Optional[str] = None
    register_number: Optional[str] = None
    patterns: Optional[str] = None
    status_ids: Optional[str] = None

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
            .join(LendingStatusModel)
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
                if self.employees_ids.find(",")
                else [self.employees_ids]
            )
            query = query.filter(EmployeeModel.id.in_(employees_ids_list))

        if self.bus:
            bus_list = self.bus.split(",") if self.bus.find(",") else [self.bus]
            query = query.filter(LendingModel.bu.in_(bus_list))

        if self.roles_ids:
            roles_ids_list = (
                self.roles_ids.split(",")
                if self.roles_ids.find(",")
                else [self.roles_ids]
            )
            query = query.filter(EmployeeModel.role.in_(roles_ids_list))

        if self.projects:
            projects_list = (
                self.projects.split(",") if self.projects.find(",") else [self.projects]
            )
            query = query.filter(LendingModel.project.in_(projects_list))

        if self.business_executive:
            business_executive_list = (
                self.business_executive.split(",")
                if self.business_executive.find(",")
                else [self.business_executive]
            )
            query = query.filter(
                LendingModel.business_executive.in_(business_executive_list)
            )

        if self.workloads_ids:
            workloads_ids_list = (
                self.workloads_ids.split(",")
                if self.workloads_ids.find(",")
                else [self.workloads_ids]
            )
            query = query.filter(WorkloadModel.id.in_(workloads_ids_list))

        if self.register_number:
            register_number_list = (
                self.register_number.split(",")
                if self.register_number.find(",")
                else [self.register_number]
            )
            query = query.filter(AssetModel.register_number.in_(register_number_list))

        if self.patterns:
            patterns_list = (
                self.patterns.split(",") if self.patterns.find(",") else [self.patterns]
            )
            query = query.filter(AssetModel.pattern.in_(patterns_list))

        if self.status_ids:
            asset_status_ids_list = (
                self.status_ids.split(",")
                if self.status_ids.find(",")
                else [self.status_ids]
            )
            query = query.filter(LendingStatusModel.id.in_(asset_status_ids_list))

        return query


class AssetReportFilter(Filter):
    """Asset report filter"""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    register_numbers: Optional[str] = None
    serial_numbers: Optional[str] = None
    patterns: Optional[str] = None
    locations: Optional[str] = None
    status_ids: Optional[str] = None
    assurance: Optional[bool] = None

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

        query = query_lending.join(AssetModel).filter(
            LendingModel.deleted.is_(False),
            or_(
                LendingModel.id.in_([lending.id for lending in previous_lending]),
            ),
        )

        if self.register_numbers:
            register_numbers_list = (
                self.register_numbers.split(",")
                if self.register_numbers.find(",")
                else [self.register_numbers]
            )
            query = query.filter(AssetModel.register_number.in_(register_numbers_list))

        if self.serial_numbers:
            serial_numbers_list = (
                self.serial_numbers.split(",")
                if self.serial_numbers.find(",")
                else [self.serial_numbers]
            )
            query = query.filter(AssetModel.serial_number.in_(serial_numbers_list))

        if self.patterns:
            patterns_list = (
                self.patterns.split(",") if self.patterns.find(",") else [self.patterns]
            )
            query = query.filter(AssetModel.pattern.in_(patterns_list))

        if self.locations:
            locations_list = (
                self.locations.split(",")
                if self.locations.find(",")
                else [self.locations]
            )
            query = query.filter(LendingModel.location.in_(locations_list))

        if self.status_ids:
            asset_status_ids_list = (
                self.status_ids.split(",")
                if self.status_ids.find(",")
                else [self.status_ids]
            )
            query = query.filter(AssetModel.status_id.in_(asset_status_ids_list))

        if self.assurance is not None:
            if self.assurance:
                query = query.filter(AssetModel.assurance_date.is_not(None))
            else:
                query = query.filter(AssetModel.assurance_date.is_(None))

        return query


class AssetPatternFilter(Filter):
    """Asset pattern filter"""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    managers: Optional[str] = None
    business_executives: Optional[str] = None
    bus: Optional[str] = None
    employees_ids: Optional[str] = None
    cost_center_ids: Optional[str] = None
    asset_type_ids: Optional[str] = None

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
            .join(CostCenterTOTVSModel)
            .join(LendingStatusModel)
            .filter(
                LendingModel.deleted.is_(False),
                LendingStatusModel.id == 2,  # active status
                or_(
                    LendingModel.id.in_([lending.id for lending in previous_lending]),
                ),
            )
        )

        if self.managers:
            managers_list = (
                self.managers.split(",") if self.managers.find(",") else [self.managers]
            )
            query = query.filter(LendingModel.manager.in_(managers_list))

        if self.business_executives:
            business_executives_list = (
                self.business_executives.split(",")
                if self.business_executives.find(",")
                else [self.business_executives]
            )
            query = query.filter(
                LendingModel.business_executive.in_(business_executives_list)
            )

        if self.bus:
            bus_list = self.bus.split(",") if self.bus.find(",") else [self.bus]
            query = query.filter(LendingModel.bu.in_(bus_list))

        if self.employees_ids:
            employees_ids_list = (
                self.employees_ids.split(",")
                if self.employees_ids.find(",")
                else [self.employees_ids]
            )
            query = query.filter(EmployeeModel.id.in_(employees_ids_list))

        if self.cost_center_ids:
            cost_center_ids_list = (
                self.cost_center_ids.split(",")
                if self.cost_center_ids.find(",")
                else [self.cost_center_ids]
            )
            query = query.filter(CostCenterTOTVSModel.id.in_(cost_center_ids_list))

        if self.asset_type_ids:
            asset_type_ids_list = (
                self.asset_type_ids.split(",")
                if self.asset_type_ids.find(",")
                else [self.asset_type_ids]
            )
            query = query.filter(AssetModel.type_id.in_(asset_type_ids_list))

        return query
