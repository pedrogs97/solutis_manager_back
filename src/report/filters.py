"""Report filters"""

import logging
from typing import List, Optional, Union

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import Select
from sqlalchemy.orm import Query
from sqlalchemy.sql.expression import and_, or_

from src.asset.models import AssetModel
from src.datasync.models import CostCenterTOTVSModel
from src.lending.models import LendingModel, LendingStatusModel, WorkloadModel
from src.log.models import LogModel
from src.maintenance.models import (
    MaintenanceActionModel,
    MaintenanceHistoricModel,
    MaintenanceModel,
    MaintenanceStatusModel,
    UpgradeHistoricModel,
)
from src.people.models import EmployeeModel
from src.utils import get_start_and_end_datetime

logger = logging.getLogger(__name__)


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
    cost_center_ids: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = LendingModel

    def filter(
        self, query_lending: Union[Query, Select], query_log: Union[Query, Select]
    ) -> Query:
        """Filter query"""
        start_datetime, end_datetime = get_start_and_end_datetime(
            self.start_date, self.end_date
        )
        previous_lending: List[LogModel] = query_log.filter(
            LogModel.model == "Lending",
            LogModel.operation.startswith("Criação"),
            LogModel.logged_in.between(start_datetime, end_datetime),
        ).all()

        query = (
            query_lending.join(AssetModel)
            .join(EmployeeModel)
            .join(WorkloadModel)
            .filter(
                and_(
                    or_(
                        LendingModel.id.in_(
                            [lending.id for lending in previous_lending]
                        ),
                        LendingModel.created_at.between(start_datetime, end_datetime),
                    ),
                    LendingModel.deleted.is_(False),
                ),
            )
        )
        try:
            if self.employees_ids:
                employees_ids_list = (
                    [int(str_id) for str_id in self.employees_ids.split(",")]
                    if "," in str(self.employees_ids)
                    else [int(self.employees_ids)]
                )
                query = query.filter(EmployeeModel.id.in_(employees_ids_list))

            if self.bus:
                bus_list = (
                    [int(str_id) for str_id in self.bus.split(",")]
                    if "," in str(self.bus)
                    else [self.bus]
                )
                query = query.filter(LendingModel.bu.in_(bus_list))

            if self.roles_ids:
                roles_ids_list = (
                    [int(str_id) for str_id in self.roles_ids.split(",")]
                    if "," in str(self.roles_ids)
                    else [int(self.roles_ids)]
                )
                query = query.filter(EmployeeModel.role.in_(roles_ids_list))

            if self.projects:
                projects_list = (
                    [int(str_id) for str_id in self.projects.split(",")]
                    if "," in str(self.projects)
                    else [self.projects]
                )
                query = query.filter(LendingModel.project.in_(projects_list))

            if self.business_executive:
                business_executive_list = (
                    [int(str_id) for str_id in self.business_executive.split(",")]
                    if "," in str(self.business_executive)
                    else [self.business_executive]
                )
                query = query.filter(
                    LendingModel.business_executive.in_(business_executive_list)
                )

            if self.workloads_ids:
                workloads_ids_list = (
                    [int(str_id) for str_id in self.workloads_ids.split(",")]
                    if "," in str(self.workloads_ids)
                    else [int(self.workloads_ids)]
                )
                query = query.filter(WorkloadModel.id.in_(workloads_ids_list))

            if self.register_number:
                register_number_list = (
                    [int(str_id) for str_id in self.register_number.split(",")]
                    if "," in str(self.register_number)
                    else [self.register_number]
                )
                query = query.filter(
                    AssetModel.register_number.in_(register_number_list)
                )

            if self.patterns:
                patterns_list = (
                    self.patterns.split(",")
                    if "," in str(self.patterns)
                    else [self.patterns]
                )
                query = query.filter(AssetModel.pattern.in_(patterns_list))

            if self.status_ids:
                asset_status_ids_list = (
                    [int(str_id) for str_id in self.status_ids.split(",")]
                    if "," in str(self.status_ids)
                    else [int(self.status_ids)]
                )
                query = query.filter(LendingModel.status_id.in_(asset_status_ids_list))

            if self.cost_center_ids:
                cost_center_ids_list = (
                    [int(str_id) for str_id in self.cost_center_ids.split(",")]
                    if "," in str(self.cost_center_ids)
                    else [int(self.cost_center_ids)]
                )
                query = query.filter(CostCenterTOTVSModel.id.in_(cost_center_ids_list))
        except ValueError as e:
            logger.warning("Error filtering query: %s", e)
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
        start_datetime, end_datetime = get_start_and_end_datetime(
            self.start_date, self.end_date
        )
        previous_lending: List[LogModel] = query_log.filter(
            LogModel.model == "Lending",
            LogModel.operation.startswith("Criação"),
            LogModel.logged_in.between(start_datetime, end_datetime),
        ).all()

        query = query_lending.join(AssetModel).filter(
            and_(
                or_(
                    LendingModel.id.in_([lending.id for lending in previous_lending]),
                    LendingModel.created_at.between(start_datetime, end_datetime),
                ),
                LendingModel.deleted.is_(False),
            ),
        )
        try:
            if self.register_numbers:
                register_numbers_list = (
                    [int(str_id) for str_id in self.register_numbers.split(",")]
                    if "," in str(self.register_numbers)
                    else [self.register_numbers]
                )
                query = query.filter(
                    AssetModel.register_number.in_(register_numbers_list)
                )

            if self.serial_numbers:
                serial_numbers_list = (
                    [int(str_id) for str_id in self.serial_numbers.split(",")]
                    if "," in str(self.serial_numbers)
                    else [self.serial_numbers]
                )
                query = query.filter(AssetModel.serial_number.in_(serial_numbers_list))

            if self.patterns:
                patterns_list = (
                    [int(str_id) for str_id in self.patterns.split(",")]
                    if "," in str(self.patterns)
                    else [self.patterns]
                )
                query = query.filter(AssetModel.pattern.in_(patterns_list))

            if self.locations:
                locations_list = (
                    [int(str_id) for str_id in self.locations.split(",")]
                    if "," in str(self.locations)
                    else [self.locations]
                )
                query = query.filter(LendingModel.location.in_(locations_list))

            if self.status_ids:
                status_ids_list = (
                    [int(str_id) for str_id in self.status_ids.split(",")]
                    if "," in str(self.status_ids)
                    else [int(self.status_ids)]
                )
                query = query.filter(LendingModel.status_id.in_(status_ids_list))

            if self.assurance is not None:
                if self.assurance:
                    query = query.filter(AssetModel.assurance_date.is_not(None))
                else:
                    query = query.filter(AssetModel.assurance_date.is_(None))
        except ValueError as e:
            logger.warning("Error filtering query: %s", e)

        return query


class AssetStockReportFilter(Filter):
    """Asset stock report filter"""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    patterns: Optional[str] = None
    status_ids: Optional[str] = None
    register_numbers: Optional[str] = None
    cost_center_ids: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = LendingModel

    def filter(
        self, query_asset: Union[Query, Select], query_log: Union[Query, Select]
    ) -> Query:
        """Filter query"""
        start_datetime, end_datetime = get_start_and_end_datetime(
            self.start_date, self.end_date
        )
        previous_lending: List[LogModel] = query_log.filter(
            LogModel.model == "Asset",
            LogModel.operation.startswith("Criação"),
            LogModel.logged_in.between(start_datetime, end_datetime),
        ).all()

        query = query_asset.filter(
            and_(
                or_(
                    AssetModel.id.in_([lending.id for lending in previous_lending]),
                    AssetModel.created_at.between(start_datetime, end_datetime),
                ),
                ~AssetModel.disposals.any(),
            ),
        )
        try:
            if self.register_numbers:
                register_numbers_list = (
                    [int(str_id) for str_id in self.register_numbers.split(",")]
                    if "," in str(self.register_numbers)
                    else [self.register_numbers]
                )
                query = query.filter(
                    AssetModel.register_number.in_(register_numbers_list)
                )

            if self.cost_center_ids:
                cost_center_ids_list = (
                    [int(str_id) for str_id in self.cost_center_ids.split(",")]
                    if "," in str(self.cost_center_ids)
                    else [int(self.cost_center_ids)]
                )
                query = query.filter(
                    LendingModel.cost_center_id.in_(cost_center_ids_list)
                )

            if self.patterns:
                patterns_list = (
                    self.patterns.split(",")
                    if "," in str(self.patterns)
                    else [self.patterns]
                )
                query = query.filter(AssetModel.pattern.in_(patterns_list))

            if self.status_ids:
                status_ids_list = (
                    [int(str_id) for str_id in self.status_ids.split(",")]
                    if "," in str(self.status_ids)
                    else [int(self.status_ids)]
                )
                query = query.filter(AssetModel.status_id.in_(status_ids_list))

        except ValueError as e:
            logger.warning("Error filtering query: %s", e)

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
    asset_types: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = LendingModel

    def filter(
        self, query_lending: Union[Query, Select], query_log: Union[Query, Select]
    ) -> Query:
        """Filter query"""
        start_datetime, end_datetime = get_start_and_end_datetime(
            self.start_date, self.end_date
        )
        previous_lending: List[LogModel] = query_log.filter(
            LogModel.model == "Lending",
            LogModel.operation.startswith("Criação"),
            LogModel.logged_in.between(start_datetime, end_datetime),
        ).all()

        query = (
            query_lending.join(AssetModel)
            .join(CostCenterTOTVSModel)
            .join(LendingStatusModel)
            .filter(
                and_(
                    or_(
                        LendingModel.id.in_(
                            [lending.id for lending in previous_lending]
                        ),
                        LendingModel.created_at.between(start_datetime, end_datetime),
                    ),
                    LendingModel.deleted.is_(False),
                ),
            )
        )

        try:
            if self.managers:
                managers_list = (
                    [int(str_id) for str_id in self.managers.split(",")]
                    if "," in str(self.managers)
                    else [self.managers]
                )
                query = query.filter(LendingModel.manager.in_(managers_list))

            if self.business_executives:
                business_executives_list = (
                    [int(str_id) for str_id in self.business_executives.split(",")]
                    if "," in str(self.business_executives)
                    else [self.business_executives]
                )
                query = query.filter(
                    LendingModel.business_executive.in_(business_executives_list)
                )

            if self.bus:
                bus_list = (
                    [int(str_id) for str_id in self.bus.split(",")]
                    if "," in str(self.bus)
                    else [self.bus]
                )
                query = query.filter(LendingModel.bu.in_(bus_list))

            if self.employees_ids:
                employees_ids_list = (
                    [int(str_id) for str_id in self.employees_ids.split(",")]
                    if "," in str(self.employees_ids)
                    else [int(self.employees_ids)]
                )
                query = query.filter(EmployeeModel.id.in_(employees_ids_list))

            if self.cost_center_ids:
                cost_center_ids_list = (
                    [int(str_id) for str_id in self.cost_center_ids.split(",")]
                    if "," in str(self.cost_center_ids)
                    else [int(self.cost_center_ids)]
                )
                query = query.filter(CostCenterTOTVSModel.id.in_(cost_center_ids_list))

            if self.asset_types:
                asset_type_ids_list = (
                    [int(str_id) for str_id in self.asset_types.split(",")]
                    if "," in str(self.asset_types)
                    else [int(self.asset_types)]
                )
                query = query.filter(AssetModel.type_id.in_(asset_type_ids_list))
        except ValueError as e:
            logger.warning("Error filtering query: %s", e)

        return query


class MaintenanceReportFilter(Filter):
    """Maintenance Report filter"""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    maintenance_type: Optional[str] = None
    maintenance_action_ids: Optional[str] = None
    patterns: Optional[str] = None
    assurance: Optional[bool] = None
    status_ids: Optional[str] = None

    class Constants(Filter.Constants):
        """Filter constants"""

        model = LendingModel

    def filter_maintenance(
        self, query_historic: Union[Query, Select], query_log: Union[Query, Select]
    ) -> Query:
        """Filter query"""
        start_datetime, end_datetime = get_start_and_end_datetime(
            self.start_date, self.end_date
        )
        previous_maintenance: List[LogModel] = query_log.filter(
            and_(
                or_(LogModel.model == "maintenance", LogModel.model == "upgrade"),
                LogModel.operation.startswith("Adição"),
                LogModel.logged_in.between(start_datetime, end_datetime),
            )
        ).all()

        query = (
            query_historic.join(MaintenanceStatusModel)
            .join(MaintenanceModel)
            .join(MaintenanceActionModel)
            .outerjoin(AssetModel)
            .filter(
                or_(
                    MaintenanceHistoricModel.maintenance_id.in_(
                        [maintenance.id for maintenance in previous_maintenance]
                    ),
                    MaintenanceHistoricModel.date.between(start_datetime, end_datetime),
                ),
            )
        )

        try:
            if self.patterns:
                patterns_list = (
                    [int(str_id) for str_id in self.patterns.split(",")]
                    if "," in str(self.patterns)
                    else [self.patterns]
                )
                query = query.filter(AssetModel.pattern.in_(patterns_list))

            if self.assurance is not None:
                query = query.filter(AssetModel.assurance_date.is_not(None))

            if self.status_ids:
                status_list = (
                    [int(str_id) for str_id in self.status_ids.split(",")]
                    if "," in str(self.status_ids)
                    else [int(self.status_ids)]
                )
                query = query.filter(AssetModel.status_id.in_(status_list))

            if self.maintenance_action_ids:
                maintenance_action_list = (
                    [int(str_id) for str_id in self.maintenance_action_ids.split(",")]
                    if "," in str(self.maintenance_action_ids)
                    else [int(self.maintenance_action_ids)]
                )
                query = query.filter(
                    MaintenanceActionModel.id.in_(maintenance_action_list)
                )

        except ValueError as e:
            logger.warning("Error filtering query: %s", e)

        return query

    def filter_upgrade(
        self, query_historic: Union[Query, Select], query_log: Union[Query, Select]
    ) -> Query:
        """Filter query"""
        start_datetime, end_datetime = get_start_and_end_datetime(
            self.start_date, self.end_date
        )
        previous_upgrade: List[LogModel] = query_log.filter(
            and_(
                or_(LogModel.model == "upgrade", LogModel.model == "upgrade"),
                LogModel.operation.startswith("Adição"),
                LogModel.logged_in.between(start_datetime, end_datetime),
            )
        ).all()

        query = (
            query_historic.join(MaintenanceStatusModel)
            .join(AssetModel)
            .filter(
                or_(
                    UpgradeHistoricModel.id.in_(
                        [upgrade.id for upgrade in previous_upgrade]
                    ),
                    UpgradeHistoricModel.date.between(start_datetime, end_datetime),
                ),
            )
        )

        try:
            if self.patterns:
                patterns_list = (
                    [int(str_id) for str_id in self.patterns.split(",")]
                    if "," in str(self.patterns)
                    else [self.patterns]
                )
                query = query.filter(AssetModel.pattern.in_(patterns_list))

            if self.assurance is not None:
                query = query.filter(AssetModel.assurance_date.is_not(None))

            if self.status:
                status_list = (
                    [int(str_id) for str_id in self.status.split(",")]
                    if "," in str(self.status)
                    else [int(self.status)]
                )
                query = query.filter(AssetModel.status_id.in_(status_list))

        except ValueError as e:
            logger.warning("Error filtering query: %s", e)

        return query
