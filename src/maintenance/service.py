"""Maintenance service"""
import logging
from datetime import date
from typing import List

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.log.services import LogService
from src.maintenance.filters import MaintenanceFilter
from src.maintenance.models import (
    MaintenanceActionModel,
    MaintenanceAttachmentModel,
    MaintenanceModel,
    MaintenanceStatusModel,
)
from src.maintenance.schemas import (
    MaintenanceActionSerializerSchema,
    MaintenanceAttachmentSerializerSchema,
    MaintenanceSerializerSchema,
    MaintenanceStatusSerializerSchema,
    NewMaintenanceSchema,
    UpdateMaintenanceSchema,
)

logger = logging.getLogger(__name__)
service_log = LogService()


class MaintenanceService:
    """Maintenance service"""

    def __get_maintenance_or_404(
        self, maintenance_id: int, db_session: Session
    ) -> MaintenanceModel:
        """Get maintenance or 404"""
        maintenance = (
            db_session.query(MaintenanceModel)
            .filter(MaintenanceModel.id == maintenance_id)
            .first()
        )
        if not maintenance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "maintenanceId",
                    "error": "Manutenção não encontrada.",
                },
            )

        return maintenance

    def __get_maintenance_action_or_404(
        self, maintenance_action_id: int, db_session: Session
    ) -> MaintenanceActionModel:
        """Get maintenance action or 404"""
        vertification_type = (
            db_session.query(MaintenanceActionModel)
            .filter(MaintenanceActionModel.id == maintenance_action_id)
            .first()
        )

        if not vertification_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "maintenanceActionId",
                    "error": "Ação de Manutenção não encontrada.",
                },
            )
        return vertification_type

    def __get_maintenance_status_or_404(
        self, maintenance_status_id: int, db_session: Session
    ) -> MaintenanceStatusModel:
        """Get maintenance status or 404"""
        maintenance_status = (
            db_session.query(MaintenanceStatusModel)
            .filter(MaintenanceStatusModel.id == maintenance_status_id)
            .first()
        )
        if not maintenance_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "maintenanceStatusId",
                    "error": "Status de manutenção não encontrado",
                },
            )

        return maintenance_status

    def serialize_maintenance_attachment(
        self, maintenance_attachment: MaintenanceAttachmentModel
    ) -> MaintenanceAttachmentSerializerSchema:
        """Serialize maintenance attachement"""
        return MaintenanceAttachmentSerializerSchema(**maintenance_attachment.__dict__)

    def serialize_maintenance(
        self, maintenance: MaintenanceModel
    ) -> MaintenanceSerializerSchema:
        """Serialize maintenance"""
        if maintenance.attachments:
            attachements = [
                self.serialize_maintenance_attachment(attachement)
                for attachement in maintenance.attachments
            ]
        else:
            attachements = []

        return MaintenanceSerializerSchema(
            **maintenance.__dict__,
            action=maintenance.action.name,
            attachments=attachements,
        )

    def serialize_maintenance_action(
        self, maintenance_action: MaintenanceActionModel
    ) -> MaintenanceActionSerializerSchema:
        """Serialize maintenance action"""
        return MaintenanceActionSerializerSchema(**maintenance_action.__dict__)

    def serialize_maintenance_status(
        self, maintenance_status: MaintenanceActionModel
    ) -> MaintenanceStatusSerializerSchema:
        """Serialize maintenance status"""
        return MaintenanceStatusSerializerSchema(**maintenance_status.__dict__)

    def create_maintenance(
        self,
        data: NewMaintenanceSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> MaintenanceSerializerSchema:
        """Creates new asset maintenance"""

        action_type = self.__get_maintenance_action_or_404(data.action_id, db_session)

        pending_status = (
            db_session.query(MaintenanceStatusModel)
            .filter(MaintenanceStatusModel.name == "Pendente")
            .first()
        )

        if not pending_status:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Sem Status de Manutenção.",
            )

        new_maintenance = MaintenanceModel(
            open_date=date.today(),
            glpi_number=data.glpi_number,
            supplier_service_order=data.supplier_service_order,
            supplier_number=data.supplier_number,
        )
        new_maintenance.status = (pending_status,)
        new_maintenance.action = (action_type,)

        db_session.add(new_maintenance)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "maintenance",
            "Adição de Manutenção",
            new_maintenance.id,
            authenticated_user,
            db_session,
        )
        logger.info("New maintenance. %s", str(new_maintenance))

        return self.serialize_maintenance(new_maintenance)

    def get_maintenance(
        self, maintenance_id: int, db_session: Session
    ) -> MaintenanceSerializerSchema:
        """Get a maintenance"""
        maintenance = self.__get_maintenance_or_404(maintenance_id, db_session)
        return self.serialize_maintenance(maintenance)

    def get_maintenances(
        self,
        db_session: Session,
        maintenance_filters: MaintenanceFilter,
        page: int = 1,
        size: int = 50,
    ) -> Page[MaintenanceSerializerSchema]:
        """Get maintenance list"""

        maintenance_list = maintenance_filters.filter(
            db_session.query(MaintenanceModel)
            .join(MaintenanceActionModel)
            .join(MaintenanceStatusModel)
        )

        params = Params(page=page, size=size)
        paginated = paginate(
            maintenance_list,
            params=params,
            transformer=lambda maintenance_list: [
                self.serialize_maintenance(lending).model_dump(by_alias=True)
                for lending in maintenance_list
            ],
        )
        return paginated

    def update_maintenance(
        self,
        data: UpdateMaintenanceSchema,
        maintenance_id: int,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> MaintenanceSerializerSchema:
        """Update a maintenance"""
        maintenance = self.__get_maintenance_or_404(maintenance_id, db_session)

        status_maintenance = self.__get_maintenance_status_or_404(
            data.status_id, db_session
        )

        maintenance.status = status_maintenance

        if data.close_date:
            maintenance.close_date = data.close_date

        if data.glpi_number:
            maintenance.glpi_number = data.glpi_number

        if data.supplier_service_order:
            maintenance.supplier_service_order = data.supplier_service_order

        if data.supplier_number:
            maintenance.supplier_number = data.supplier_number

        if data.resolution:
            maintenance.resolution = data.resolution

        db_session.add(maintenance)
        db_session.commit()

        service_log.set_log(
            "lending",
            "maintenance",
            "Atualiação de Manutenção",
            maintenance.id,
            authenticated_user,
            db_session,
        )
        logger.info("Update maintenance. %s", str(maintenance))

        return self.serialize_maintenance(maintenance)

    def get_maintenance_actions(
        self, db_session: Session
    ) -> List[MaintenanceActionSerializerSchema]:
        """Get maintenance actions"""

        maintenance_actions = db_session.query(MaintenanceActionModel).all()
        return [
            self.serialize_maintenance_action(action).model_dump(by_alias=True)
            for action in maintenance_actions
        ]

    def get_maintenance_status(
        self, db_session: Session
    ) -> List[MaintenanceStatusSerializerSchema]:
        """Get maintenance status"""

        maintenance_status = db_session.query(MaintenanceActionModel).all()
        return [
            self.serialize_maintenance_status(status).model_dump(by_alias=True)
            for status in maintenance_status
        ]
