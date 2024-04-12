"""Maintenance service"""

import logging
import os
from datetime import date, timedelta
from typing import List

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.asset.models import AssetModel
from src.asset.schemas import AssetShortSerializerSchema
from src.auth.models import UserModel
from src.backends import Email365Client, get_db_session
from src.config import ATTACHMENTS_UPLOAD_DIR, DEFAULT_DATE_FORMAT
from src.log.services import LogService
from src.maintenance.filters import MaintenanceFilter, UpgradeFilter
from src.maintenance.models import (
    MaintenanceActionModel,
    MaintenanceAttachmentModel,
    MaintenanceCriticalityModel,
    MaintenanceHistoricModel,
    MaintenanceModel,
    MaintenanceStatusModel,
    UpgradeAttachmentModel,
    UpgradeHistoricModel,
    UpgradeModel,
)
from src.maintenance.schemas import (
    MaintenanceActionSerializerSchema,
    MaintenanceAttachmentSerializerSchema,
    MaintenanceCriticalityModelSerializerSchema,
    MaintenanceSerializerSchema,
    MaintenanceStatusSerializerSchema,
    NewMaintenanceSchema,
    NewUpgradeSchema,
    UpdateMaintenanceSchema,
    UpdateUpgradeSchema,
    UpgradeAttachmentSerializerSchema,
    UpgradeSerializerSchema,
)
from src.people.models import EmployeeModel
from src.people.schemas import EmployeeShortSerializerSchema
from src.utils import upload_file

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
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "maintenanceId",
                    "error": "Manutenção não encontrada.",
                },
            )

        return maintenance

    def __get_attachment_or_404(
        self, attachment_id: int, db_session: Session
    ) -> MaintenanceAttachmentModel:
        """Get attachment or 404"""
        attachment = (
            db_session.query(MaintenanceAttachmentModel)
            .filter(MaintenanceAttachmentModel.id == attachment_id)
            .first()
        )
        if not attachment:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "attachmentId",
                    "error": "Anexo de Manutenção não encontrada.",
                },
            )

        return attachment

    def __get_maintenance_action_or_404(
        self, maintenance_action_id: int, db_session: Session
    ) -> MaintenanceActionModel:
        """Get maintenance action or 404"""
        maintenance_action = (
            db_session.query(MaintenanceActionModel)
            .filter(MaintenanceActionModel.id == maintenance_action_id)
            .first()
        )

        if not maintenance_action:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "maintenanceActionId",
                    "error": "Ação de Manutenção não encontrada.",
                },
            )
        return maintenance_action

    def __get_maintenance_criticality_or_404(
        self, maintenance_criticality_id: int, db_session: Session
    ) -> MaintenanceCriticalityModel:
        """Get maintenance criticality or 404"""
        maintenance_criticality = (
            db_session.query(MaintenanceCriticalityModel)
            .filter(MaintenanceCriticalityModel.id == maintenance_criticality_id)
            .first()
        )

        if not maintenance_criticality:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "maintenanceCriticalityId",
                    "error": "Ação de Manutenção não encontrada.",
                },
            )
        return maintenance_criticality

    def __get_asset_or_404(self, asset_id: int, db_session: Session) -> AssetModel:
        """Get asset or 404"""
        asset = db_session.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if not asset:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "assetId", "error": "Ativo não encontrado"},
            )

        return asset

    def __get_employee_or_404(
        self, employee_id: int, db_session: Session
    ) -> EmployeeModel:
        """Get employee or 404"""
        employee = (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.id == employee_id)
            .first()
        )
        if not employee:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "employeeId", "error": "Colaborador não encontrado"},
            )
        return employee

    def __generate_so_supplier(self, db_session: Session) -> str:
        """Generate new service order supplier"""
        default_code = 1

        last_maintenance = (
            db_session.query(MaintenanceModel)
            .order_by(MaintenanceModel.id.desc())
            .first()
        )

        if last_maintenance:
            code = str(default_code + last_maintenance.id)

            asset_acronym = (
                last_maintenance.asset.type.acronym
                if last_maintenance.asset.type
                else last_maintenance.asset.description[:3]
            )

            return f"MA{asset_acronym}" + code.zfill(16 - len(code))

    def serialize_maintenance_attachment(
        self, maintenance_attachment: MaintenanceAttachmentModel
    ) -> MaintenanceAttachmentSerializerSchema:
        """Serialize maintenance attachement"""
        return MaintenanceAttachmentSerializerSchema(**maintenance_attachment.__dict__)

    def serialize_maintenance_criticality(
        self, criticality: MaintenanceCriticalityModel
    ) -> MaintenanceCriticalityModelSerializerSchema:
        """Serialize maintenance criticality"""
        return MaintenanceCriticalityModelSerializerSchema(**criticality.__dict__)

    def serialize_maintenance(
        self, maintenance: MaintenanceModel
    ) -> MaintenanceSerializerSchema:
        """Serialize maintenance"""
        attachements = []
        if maintenance.attachments:
            attachements = [
                self.serialize_maintenance_attachment(attachement)
                for attachement in maintenance.attachments
            ]

        return MaintenanceSerializerSchema(
            id=maintenance.id,
            action=MaintenanceActionSerializerSchema(**maintenance.action.__dict__),
            status=maintenance.status.name,
            attachments=attachements,
            close_date=(
                maintenance.close_date.strftime(DEFAULT_DATE_FORMAT)
                if maintenance.close_date
                else None
            ),
            glpi_number=maintenance.glpi_number,
            open_date=maintenance.open_date.strftime(DEFAULT_DATE_FORMAT),
            resolution=maintenance.resolution,
            supplier_number=maintenance.supplier_number,
            supplier_service_order=maintenance.supplier_service_order,
            asset=AssetShortSerializerSchema(
                asset_type=(
                    maintenance.asset.type.name if maintenance.asset.type else None
                ),
                description=maintenance.asset.description,
                id=maintenance.asset.id,
                register_number=maintenance.asset.register_number,
            ),
            employee=EmployeeShortSerializerSchema(
                code=maintenance.employee.code,
                id=maintenance.employee.id,
                full_name=maintenance.employee.full_name,
                registration=maintenance.employee.registration,
            ),
            open_date_supplier=(
                maintenance.open_date_supplier.strftime(DEFAULT_DATE_FORMAT)
                if maintenance.open_date_supplier
                else None
            ),
            open_date_glpi=(
                maintenance.open_date_glpi.strftime(DEFAULT_DATE_FORMAT)
                if maintenance.open_date_glpi
                else None
            ),
            incident_description=maintenance.incident_description,
            value=maintenance.value if maintenance.value else float(0.0),
            criticality=(
                self.serialize_maintenance_criticality(maintenance.criticality)
                if maintenance.criticality
                else None
            ),
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

        asset = self.__get_asset_or_404(data.asset_id, db_session)

        employee = self.__get_employee_or_404(data.employee_id, db_session)

        criticality = self.__get_maintenance_criticality_or_404(
            data.criticality_id, db_session
        )

        pending_status = (
            db_session.query(MaintenanceStatusModel)
            .filter(MaintenanceStatusModel.name == "Pendente")
            .first()
        )

        if not pending_status:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Sem Status de Manutenção.",
            )

        supplier_so = self.__generate_so_supplier(db_session)

        new_maintenance = MaintenanceModel(
            open_date=date.today(),
            glpi_number=data.glpi_number,
            supplier_service_order=supplier_so,
            supplier_number=data.supplier_number,
            open_date_glpi=data.open_date_glpi,
            open_date_supplier=data.open_date_supplier,
            incident_description=data.incident_description,
            resolution=data.resolution,
            value=data.value,
            criticality=criticality,
        )
        new_maintenance.status = pending_status
        new_maintenance.action = action_type
        new_maintenance.asset = asset
        new_maintenance.employee = employee

        db_session.add(new_maintenance)
        db_session.commit()
        db_session.flush()

        historic = MaintenanceHistoricModel(
            maintenance_id=new_maintenance.id,
            status_id=pending_status.id,
            date=date.today(),
        )
        db_session.add(historic)
        db_session.commit()

        service_log.set_log(
            "asset",
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
            .join(AssetModel)
        ).order_by(desc(MaintenanceModel.id))

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

        if data.in_progress:
            maintenance.status_id = 1

        if data.close:
            maintenance.close_date = date.today()
            maintenance.status_id = 3

        if data.open_date_supplier:
            maintenance.open_date_supplier = data.open_date_supplier

        if data.supplier_number:
            maintenance.supplier_number = data.supplier_number

        if data.resolution:
            maintenance.resolution = data.resolution

        if data.criticality_id:
            maintenance.criticality_id = data.criticality_id

        if data.value:
            maintenance.value = data.value

        db_session.add(maintenance)
        db_session.commit()
        db_session.flush()

        historic = MaintenanceHistoricModel(
            maintenance_id=maintenance.id,
            status_id=maintenance.status_id,
            date=date.today(),
        )
        db_session.add(historic)
        db_session.commit()

        service_log.set_log(
            "asset",
            "maintenance",
            "Atualiação de Manutenção",
            maintenance.id,
            authenticated_user,
            db_session,
        )
        logger.info("Update maintenance. %s", str(maintenance))

        return self.serialize_maintenance(maintenance)

    def get_maintenance_actions(self, db_session: Session) -> List[dict]:
        """Get maintenance actions"""

        maintenance_actions = (
            db_session.query(MaintenanceActionModel)
            .order_by(desc(MaintenanceActionModel.id))
            .all()
        )
        return [
            self.serialize_maintenance_action(action).model_dump(by_alias=True)
            for action in maintenance_actions
        ]

    def get_maintenance_status(self, db_session: Session) -> List[dict]:
        """Get maintenance status"""

        maintenance_status = (
            db_session.query(MaintenanceStatusModel)
            .order_by(desc(MaintenanceStatusModel.id))
            .all()
        )
        return [
            self.serialize_maintenance_status(status).model_dump(by_alias=True)
            for status in maintenance_status
        ]

    def get_maintenance_criticality(self, db_session: Session) -> List[dict]:
        """Get maintenance criticality"""

        maintenance_criticality = (
            db_session.query(MaintenanceCriticalityModel)
            .order_by(desc(MaintenanceCriticalityModel.id))
            .all()
        )
        return [
            self.serialize_maintenance_criticality(criticality).model_dump(
                by_alias=True
            )
            for criticality in maintenance_criticality
        ]

    async def upload_attachments(
        self,
        attachments: List[UploadFile],
        maintenanceId: int,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> List[MaintenanceAttachmentSerializerSchema]:
        """Upload attachments"""

        return_list = []
        attachments_to_add = []

        for attach in attachments:
            file_name = f"{attach.filename}"
            file_path = await upload_file(
                file_name,
                os.path.join("maintenance", str(maintenanceId)),
                attach.file.read(),
                ATTACHMENTS_UPLOAD_DIR,
            )

            new_attach = MaintenanceAttachmentModel(path=file_path, file_name=file_name)
            new_attach.maintenance_id = maintenanceId
            attachments_to_add.append(new_attach)

        db_session.add_all(attachments_to_add)
        db_session.commit()
        db_session.flush()

        for attch_added in attachments_to_add:
            service_log.set_log(
                "asset",
                "maintenance_attachment",
                "Importação de Anexos de Manutenção",
                new_attach.id,
                authenticated_user,
                db_session,
            )
            logger.info("Upload Attachment. %s", str(attch_added))
            return_list.append(self.serialize_maintenance_attachment(attch_added))

        return return_list

    def get_attachment(
        self, attachment_id, db_session: Session
    ) -> MaintenanceAttachmentSerializerSchema:
        """Get an attachment maintenance"""
        attachment = self.__get_attachment_or_404(attachment_id, db_session)
        return self.serialize_maintenance_attachment(attachment)

    @staticmethod
    def check_pending_maintenances() -> None:
        """Check pending maintenances"""
        db_session = get_db_session()
        later_date = date.today() - timedelta(days=15)
        pending_maintenances = (
            db_session.query(MaintenanceModel)
            .join(MaintenanceStatusModel)
            .filter(
                MaintenanceStatusModel.name == "Pendente",
                MaintenanceModel.updated_at <= later_date,
            )
            .all()
        )

        for maintenance in pending_maintenances:
            if maintenance.employee and maintenance.employee.email:
                email_client = Email365Client(
                    maintenance.employee.email,
                    "Manutenção Pendente",
                    "notify_maintenance",
                    {
                        "id": maintenance.asset.id,
                        "full_name": maintenance.employee.full_name,
                        "asset_type": (
                            maintenance.asset.type.name
                            if maintenance.asset.type
                            else "Ativo"
                        ),
                        "type": "Manutenção",
                    },
                )
                email_client.send_message()
        db_session.close()


class UpgradeService:
    """Upgrade service"""

    def __get_upgrade_or_404(
        self, upgrade_id: int, db_session: Session
    ) -> UpgradeModel:
        """Get upgrade or 404"""
        upgrade = (
            db_session.query(UpgradeModel).filter(UpgradeModel.id == upgrade_id).first()
        )
        if not upgrade:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "upgradeId",
                    "error": "Melhoria não encontrada.",
                },
            )

        return upgrade

    def __get_attachment_or_404(
        self, attachment_id: int, db_session: Session
    ) -> UpgradeAttachmentModel:
        """Get attachment or 404"""
        attachment = (
            db_session.query(UpgradeAttachmentModel)
            .filter(UpgradeAttachmentModel.id == attachment_id)
            .first()
        )
        if not attachment:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "attachmentId",
                    "error": "Anexo de Melhoria não encontrada.",
                },
            )

        return attachment

    def __get_asset_or_404(self, asset_id: int, db_session: Session) -> AssetModel:
        """Get asset or 404"""
        asset = db_session.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if not asset:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "assetId", "error": "Ativo não encontrado"},
            )

        return asset

    def __get_employee_or_404(
        self, employee_id: int, db_session: Session
    ) -> EmployeeModel:
        """Get employee or 404"""
        employee = (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.id == employee_id)
            .first()
        )
        if not employee:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "employeeId", "error": "Colaborador não encontrado"},
            )
        return employee

    def serialize_upgrade_attachment(
        self, upgrade_attachment: UpgradeModel
    ) -> UpgradeAttachmentSerializerSchema:
        """Serialize upgrade attachement"""
        return UpgradeAttachmentSerializerSchema(**upgrade_attachment.__dict__)

    def serialize_upgrade(self, upgrade: UpgradeModel) -> UpgradeSerializerSchema:
        """Serialize upgrade"""

        attachements = []
        if upgrade.attachments:
            attachements = [
                self.serialize_upgrade_attachment(attachement)
                for attachement in upgrade.attachments
            ]

        return UpgradeSerializerSchema(
            close_date=(
                upgrade.close_date.strftime(DEFAULT_DATE_FORMAT)
                if upgrade.close_date
                else None
            ),
            asset=AssetShortSerializerSchema(
                asset_type=upgrade.asset.type.name if upgrade.asset.type else None,
                id=upgrade.asset.id,
                description=upgrade.asset.description,
                register_number=upgrade.asset.register_number,
            ),
            id=upgrade.id,
            detailing=upgrade.detailing,
            employee=EmployeeShortSerializerSchema(
                code=upgrade.employee.code,
                full_name=upgrade.employee.full_name,
                id=upgrade.employee.id,
                registration=upgrade.employee.registration,
            ),
            value=upgrade.value,
            observations=upgrade.observations,
            open_date=upgrade.open_date.strftime(DEFAULT_DATE_FORMAT),
            status=upgrade.status.name,
            supplier=upgrade.supplier,
            attachments=attachements,
            invoice_number=upgrade.invoice_number,
        )

    def create_upgrade(
        self,
        data: NewUpgradeSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> UpgradeSerializerSchema:
        """Creates new asset upgrade"""
        asset = self.__get_asset_or_404(data.asset_id, db_session)

        employee = self.__get_employee_or_404(data.employee_id, db_session)

        pending_status = (
            db_session.query(MaintenanceStatusModel)
            .filter(MaintenanceStatusModel.name == "Pendente")
            .first()
        )

        if not pending_status:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Sem Status de Manutenção.",
            )

        new_upgrade = UpgradeModel(
            open_date=date.today(),
            value=data.value,
            detailing=data.detailing,
            supplier=data.supplier,
            observations=data.observations,
            invoice_number=data.invoice_number,
        )
        new_upgrade.status = pending_status
        new_upgrade.asset = asset
        new_upgrade.employee = employee

        db_session.add(new_upgrade)
        db_session.commit()
        db_session.flush()

        historic = UpgradeHistoricModel(
            maintenance_id=new_upgrade.id,
            status_id=pending_status.id,
            date=date.today(),
        )
        db_session.add(historic)
        db_session.commit()

        service_log.set_log(
            "asset",
            "upgrade",
            "Adição de Melhoria",
            new_upgrade.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Upgrade. %s", str(new_upgrade))

        return self.serialize_upgrade(new_upgrade)

    def get_upgrade(
        self, upgrade_id: int, db_session: Session
    ) -> UpgradeSerializerSchema:
        """Get an upgrade"""
        upgrade = self.__get_upgrade_or_404(upgrade_id, db_session)
        return self.serialize_upgrade(upgrade)

    def get_upgrades(
        self,
        db_session: Session,
        upgrade_filters: UpgradeFilter,
        page: int = 1,
        size: int = 50,
    ) -> Page[UpgradeSerializerSchema]:
        """Get upgrade list"""

        upgrade_list = upgrade_filters.filter(
            db_session.query(UpgradeModel).join(MaintenanceStatusModel).join(AssetModel)
        ).order_by(desc(UpgradeModel.id))

        params = Params(page=page, size=size)
        paginated = paginate(
            upgrade_list,
            params=params,
            transformer=lambda upgrade_list: [
                self.serialize_upgrade(upgrade).model_dump(by_alias=True)
                for upgrade in upgrade_list
            ],
        )
        return paginated

    def update_upgrade(
        self,
        data: UpdateUpgradeSchema,
        upgrade_id: int,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> UpgradeSerializerSchema:
        """Update a upgrade"""
        upgrade = self.__get_upgrade_or_404(upgrade_id, db_session)

        if data.in_progress:
            upgrade.status_id = 1

        if data.close:
            upgrade.close_date = date.today()
            upgrade.status_id = 3

        if data.detailing:
            upgrade.detailing = data.detailing

        if data.observations:
            upgrade.observations = data.observations

        if data.invoice_number:
            upgrade.invoice_number = data.invoice_number

        if data.value:
            upgrade.value = float(data.value)

        db_session.add(upgrade)
        db_session.commit()
        db_session.flush()

        historic = UpgradeHistoricModel(
            maintenance_id=upgrade.id,
            status_id=upgrade.status_id,
            date=date.today(),
        )
        db_session.add(historic)
        db_session.commit()

        service_log.set_log(
            "asset",
            "upgrade",
            "Atualiação de Melhoria",
            upgrade.id,
            authenticated_user,
            db_session,
        )
        logger.info("Update Upgrade. %s", str(upgrade))

        return self.serialize_upgrade(upgrade)

    async def upload_attachments(
        self,
        attachments: List[UploadFile],
        upgradeId: int,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> List[UpgradeAttachmentSerializerSchema]:
        """Upload attachments"""

        return_list = []
        attachments_to_add = []

        for attach in attachments:
            file_name = f"{attach.filename}"
            file_path = await upload_file(
                file_name,
                os.path.join("upgrade", str(upgradeId)),
                attach.file.read(),
                ATTACHMENTS_UPLOAD_DIR,
            )

            new_attach = UpgradeAttachmentModel(path=file_path, file_name=file_name)
            new_attach.upgrade_id = upgradeId
            attachments_to_add.append(new_attach)

        db_session.add_all(attachments_to_add)
        db_session.commit()
        db_session.flush()

        for attch_added in attachments_to_add:
            service_log.set_log(
                "asset",
                "upgrade_attachment",
                "Importação de Anexos de Melhoria",
                new_attach.id,
                authenticated_user,
                db_session,
            )
            logger.info("Upload Attachment. %s", str(attch_added))
            return_list.append(self.serialize_upgrade_attachment(attch_added))

        return return_list

    def get_attachment(
        self, attachment_id, db_session: Session
    ) -> UpgradeAttachmentSerializerSchema:
        """Get an attachment maintenance"""
        attachment = self.__get_attachment_or_404(attachment_id, db_session)
        return self.serialize_upgrade_attachment(attachment)

    @staticmethod
    def check_pending_upgrades() -> None:
        """Check pending upgrades"""
        db_session = get_db_session()
        later_date = date.today() - timedelta(days=15)
        pending_upgrades = (
            db_session.query(UpgradeModel)
            .join(MaintenanceStatusModel)
            .filter(
                MaintenanceStatusModel.name == "Pendente",
                UpgradeModel.updated_at <= later_date,
            )
            .all()
        )

        for upgrade in pending_upgrades:
            if upgrade.employee and upgrade.employee.email:
                email_client = Email365Client(
                    upgrade.employee.email,
                    "Melhoria Pendente",
                    "notify_maintenance",
                    {
                        "id": upgrade.asset.id,
                        "full_name": upgrade.employee.full_name,
                        "asset_type": (
                            upgrade.asset.type.name if upgrade.asset.type else "Ativo"
                        ),
                        "type": "Melhoria",
                    },
                )
                email_client.send_message()
        db_session.close()
