"""Lenging service"""

import locale
import logging
from typing import List

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.asset.models import AssetModel, AssetStatusModel, AssetTypeModel
from src.asset.schemas import AssetShortSerializerSchema
from src.auth.models import UserModel
from src.config import DEFAULT_DATE_FORMAT
from src.datasync.models import CostCenterTOTVSModel
from src.lending.filters import LendingFilter, WorkloadFilter
from src.lending.models import (
    LendingModel,
    LendingStatusModel,
    WitnessModel,
    WorkloadModel,
)
from src.lending.schemas import (
    CostCenterSerializerSchema,
    CreateWitnessSchema,
    LendingSerializerSchema,
    NewLendingSchema,
    UpdateLendingSchema,
    WitnessSerializerSchema,
    WorkloadSerializerSchema,
)
from src.log.services import LogService
from src.people.models import EmployeeModel
from src.people.schemas import (
    EmployeeEducationalLevelSerializerSchema,
    EmployeeGenderSerializerSchema,
    EmployeeMatrimonialStatusSerializerSchema,
    EmployeeNationalitySerializerSchema,
    EmployeeRoleSerializerSchema,
    EmployeeSerializerSchema,
)

logger = logging.getLogger(__name__)
service_log = LogService()
locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")


class LendingService:
    """Lending service"""

    def __get_lending_or_404(
        self, lending_id: int, db_session: Session
    ) -> LendingModel:
        """Get lending or 404"""
        lending = (
            db_session.query(LendingModel).filter(LendingModel.id == lending_id).first()
        )
        if not lending:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "lendingId",
                    "error": "Contrato de Comodato não encontrado",
                },
            )

        return lending

    def serialize_employee(self, employee: EmployeeModel) -> EmployeeSerializerSchema:
        """Serializer employee"""
        return EmployeeSerializerSchema(
            id=employee.id,
            role=(
                EmployeeRoleSerializerSchema(**employee.role.__dict__)
                if employee.role
                else None
            ),
            nationality=EmployeeNationalitySerializerSchema(
                **employee.nationality.__dict__
            ),
            marital_status=EmployeeMatrimonialStatusSerializerSchema(
                **employee.marital_status.__dict__
            ),
            gender=EmployeeGenderSerializerSchema(**employee.gender.__dict__),
            educational_level=(
                EmployeeEducationalLevelSerializerSchema(
                    **employee.educational_level.__dict__
                )
                if employee.educational_level
                else None
            ),
            status=employee.status,
            manager=employee.manager,
            address=employee.address,
            birthday=employee.birthday.strftime(DEFAULT_DATE_FORMAT),
            cell_phone=employee.cell_phone,
            code=employee.code,
            email=employee.email,
            full_name=employee.full_name,
            legal_person=employee.legal_person,
            national_identification=employee.national_identification,
            taxpayer_identification=employee.taxpayer_identification,
            admission_date=(
                employee.admission_date.strftime(DEFAULT_DATE_FORMAT)
                if employee.admission_date
                else None
            ),
        )

    def serialize_witness(self, witness: WitnessModel) -> WitnessSerializerSchema:
        """Serialize witness"""
        employee_serializer = self.serialize_employee(witness.employee)

        return WitnessSerializerSchema(
            id=witness.id,
            employee=employee_serializer,
        )

    def serialize_lending(self, lending: LendingModel) -> LendingSerializerSchema:
        """Serialize lending"""
        witnesses_serialzier = []

        for witness in lending.witnesses:
            witnesses_serialzier.append(self.serialize_witness(witness))

        asset_short = AssetShortSerializerSchema(
            id=lending.asset.id,
            asset_type=lending.asset.type.name,
            description=lending.asset.description,
            register_number=lending.asset.register_number,
        )

        return LendingSerializerSchema(
            id=lending.id,
            employee=self.serialize_employee(lending.employee),
            asset=asset_short,
            document=lending.document.id if lending.document else None,
            document_revoke=(
                lending.document_revoke.id if lending.document_revoke else None
            ),
            workload=(
                WorkloadSerializerSchema(**lending.workload.__dict__)
                if lending.workload
                else None
            ),
            witnesses=witnesses_serialzier,
            cost_center=CostCenterSerializerSchema(**lending.cost_center.__dict__),
            manager=lending.manager,
            observations=lending.observations,
            signed_date=(
                lending.signed_date.strftime(DEFAULT_DATE_FORMAT)
                if lending.signed_date
                else None
            ),
            revoke_signed_date=(
                lending.revoke_signed_date.strftime(DEFAULT_DATE_FORMAT)
                if lending.revoke_signed_date
                else None
            ),
            glpi_number=lending.glpi_number,
            status=lending.status.name if lending.status else "",
            business_executive=lending.business_executive,
            project=lending.project,
            location=lending.location,
            number=lending.number,
            bu=lending.bu,
            deleted=lending.deleted,
            ms_office=lending.ms_office,
        )

    def serialize_workload(self, workload: WorkloadModel) -> WorkloadSerializerSchema:
        """Serialize workload"""
        return WorkloadSerializerSchema(**workload.__dict__)

    def __validate_nested(self, data: NewLendingSchema, db_session: Session) -> tuple:
        """Validates employee, asset, workload, cost center and document values"""
        errors = []
        if data.employee_id:
            employee = (
                db_session.query(EmployeeModel)
                .filter(EmployeeModel.id == data.employee_id)
                .first()
            )
            if not employee:
                errors.append(
                    {
                        "field": "employeeId",
                        "error": f"Tipo de Colaborador não existe. {employee}",
                    }
                )

        if data.asset_id:
            asset = (
                db_session.query(AssetModel)
                .filter(AssetModel.id == data.asset_id)
                .first()
            )
            if not asset:
                errors.append(
                    {"field": "assetId", "error": f"Ativo não existe. {data.asset_id}"}
                )

            if not asset.type:
                errors.append(
                    {
                        "field": "assetId",
                        "error": "Ativo não possui Tipo. Altere o Ativo.",
                    }
                )
            else:
                if asset.status.id == 2:
                    linked_lending = (
                        db_session.query(LendingModel)
                        .join(AssetModel)
                        .filter(AssetModel.id == data.asset_id)
                        .first()
                    )
                    errors.append(
                        {
                            "field": "assetId",
                            "error": f"Ativo já está vinculado a um comodato. {linked_lending}",
                        }
                    )

                if asset.status.id == 6:
                    errors.append(
                        {
                            "field": "assetId",
                            "error": f"Ativo está inativo. {asset}",
                        }
                    )

                if asset.status.id == 5:
                    errors.append(
                        {
                            "field": "assetId",
                            "error": f"Ativo está reservado. {asset}",
                        }
                    )

                if asset.status.id == 8:
                    errors.append(
                        {
                            "field": "assetId",
                            "error": f"Ativo descartado. {asset}",
                        }
                    )

                if asset.status.id == 7:
                    errors.append(
                        {
                            "field": "assetId",
                            "error": f"Ativo emprestado. {asset}",
                        }
                    )

        workload = None
        if data.workload_id:
            workload = (
                db_session.query(WorkloadModel)
                .filter(WorkloadModel.id == data.workload_id)
                .first()
            )
            if not workload:
                errors.append(
                    {"field": "workloadId", "error": f"Lotação não existe. {workload}"}
                )

        if data.cost_center_id:
            cost_center = (
                db_session.query(CostCenterTOTVSModel)
                .filter(CostCenterTOTVSModel.id == data.cost_center_id)
                .first()
            )
            if not cost_center:
                errors.append(
                    {
                        "field": "costCenter",
                        "error": f"Centro de Custo não existe. {cost_center}",
                    }
                )

        witnesses = []
        if data.witnesses_id:
            ids_not_found = []
            for witness in data.witnesses_id:
                employee_obj = (
                    db_session.query(EmployeeModel)
                    .filter(EmployeeModel.id == witness)
                    .first()
                )

                if not employee_obj:
                    ids_not_found.append(witness)
                else:
                    new_witness = WitnessModel(employee=employee_obj)
                    db_session.add(new_witness)
                    db_session.commit()
                    db_session.flush()
                    witnesses.append(new_witness)

            if ids_not_found:
                errors.append(
                    {
                        "field": "witnessId",
                        "error": {"Testemunhas não encontradas": ids_not_found},
                    }
                )

        if errors:
            db_session.close()
            raise HTTPException(
                detail=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return (
            employee,
            asset,
            workload,
            cost_center,
            witnesses,
        )

    def create_lending(
        self,
        new_lending: NewLendingSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ):
        """Creates new lending"""
        try:
            (
                employee,
                asset,
                workload,
                cost_center,
                witnesses,
            ) = self.__validate_nested(new_lending, db_session)

            lending_pending = (
                db_session.query(LendingStatusModel)
                .filter(LendingStatusModel.name == "Arquivo pendente")
                .first()
            )

            new_lending_db = LendingModel(
                manager=new_lending.manager,
                observations=new_lending.observations,
                glpi_number=new_lending.glpi_number,
                business_executive=new_lending.business_executive,
                project=new_lending.project,
                location=new_lending.location,
                bu=new_lending.bu,
                ms_office=new_lending.ms_office,
            )

            asset.status = db_session.query(AssetStatusModel).get(2)
            db_session.add(asset)
            db_session.commit()
            db_session.flush()

            new_lending_db.employee = employee
            new_lending_db.asset = asset
            new_lending_db.workload = workload
            new_lending_db.cost_center = cost_center
            new_lending_db.status = lending_pending

            new_lending_db.witnesses = witnesses
            db_session.add(new_lending_db)
            db_session.commit()
            db_session.flush()

            service_log.set_log(
                "lending",
                "lending",
                "Criação de Comodato",
                new_lending_db.id,
                authenticated_user,
                db_session,
            )
            logger.info("New Lending. %s", str(new_lending_db))

            return self.serialize_lending(new_lending_db)
        except TypeError as error:
            db_session.rollback()
            logger.error("Error creating lending. %s", error)
            raise HTTPException(
                detail={
                    "field": "employeeId",
                    "error": "Erro ao criar contrato de comodato",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from error

    def get_lending(
        self, lending_id: int, db_session: Session
    ) -> LendingSerializerSchema:
        """Get a lending"""
        lending = self.__get_lending_or_404(lending_id, db_session)
        return self.serialize_lending(lending)

    def update_lending(
        self,
        lending_id: int,
        data: UpdateLendingSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> LendingSerializerSchema:
        """Update a lending"""
        lending = self.__get_lending_or_404(lending_id, db_session)

        lending.observations = data.observations

        for key, value in data.model_dump().items():
            if value is not None:
                setattr(lending, key, value)

        db_session.add(lending)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "lending",
            "Atualização de Comodato",
            lending.id,
            authenticated_user,
            db_session,
        )
        logger.info("Update Lending. %s", str(lending))

        return self.serialize_lending(lending)

    def get_lendings(
        self,
        db_session: Session,
        lending_filters: LendingFilter,
        page: int = 1,
        size: int = 50,
    ) -> Page[LendingSerializerSchema]:
        """Get lendings list"""

        lending_list = (
            lending_filters.filter(
                db_session.query(LendingModel)
                .outerjoin(EmployeeModel)
                .outerjoin(AssetModel)
                .outerjoin(AssetTypeModel)
                .outerjoin(WorkloadModel)
                .outerjoin(CostCenterTOTVSModel)
                .outerjoin(LendingStatusModel)
            )
            .filter(LendingModel.deleted.is_(False))
            .order_by(desc(LendingModel.id))
        )

        params = Params(page=page, size=size)
        paginated = paginate(
            lending_list,
            params=params,
            transformer=lambda lending_list: [
                self.serialize_lending(lending).model_dump(by_alias=True)
                for lending in lending_list
            ],
        )
        return paginated

    def get_workloads(
        self,
        db_session: Session,
        workload_filters: WorkloadFilter,
        fields: str = "",
    ) -> List[WorkloadSerializerSchema]:
        """Get workloads list"""

        workloads_list = workload_filters.filter(
            db_session.query(WorkloadModel)
        ).order_by(desc(WorkloadModel.id))

        if fields == "":
            return [
                self.serialize_workload(workload).model_dump(by_alias=True)
                for workload in workloads_list
            ]

        list_fields = fields.split(",")
        return [
            self.serialize_workload(workload).model_dump(
                include={*list_fields}, by_alias=True
            )
            for workload in workloads_list
        ]

    def create_witness(
        self,
        data: CreateWitnessSchema,
        authenticated_user: UserModel,
        db_session: Session,
    ) -> WitnessSerializerSchema:
        """Creates new witness"""
        employee = (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.id == data.employee_id)
            .first()
        )

        if not employee:
            db_session.close()
            raise HTTPException(
                detail={
                    "field": "employeeId",
                    "error": "Colaborador não encontrado",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        new_witness = WitnessModel(employee=employee)
        db_session.add(new_witness)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "witness",
            "Criação de Testemunha",
            new_witness.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Witness. %s", str(new_witness))

        return self.serialize_witness(new_witness)

    def get_witnesses(
        self,
        db_session: Session,
        witnesses_filters: WorkloadFilter,
        fields: str = "",
    ) -> List[WitnessSerializerSchema]:
        """Get witnesses list"""

        witnesses_list = witnesses_filters.filter(
            db_session.query(WitnessModel).join(EmployeeModel)
        ).order_by(desc(WitnessModel.id))

        if fields == "":
            return [
                self.serialize_witness(witnesss).model_dump(by_alias=True)
                for witnesss in witnesses_list
            ]

        list_fields = fields.split(",")
        return [
            self.serialize_witness(witnesss).model_dump(
                include={*list_fields}, by_alias=True
            )
            for witnesss in witnesses_list
        ]

    def delete_lending(
        self, lending_id: int, authenticated_user: UserModel, db_session: Session
    ) -> None:
        """Remove a lending"""
        try:
            lending = self.__get_lending_or_404(lending_id, db_session)
            lending.deleted = True

            if lending.document:
                lending.document.deleted = True
                db_session.add(lending.document)

            lending.asset.status = db_session.query(AssetStatusModel).get(1)
            db_session.add(lending.asset)
            db_session.add(lending)
            db_session.commit()
            db_session.flush()
            service_log.set_log(
                "lending",
                "lending",
                "Exclusão de Comodato",
                lending.id,
                authenticated_user,
                db_session,
            )
            logger.info("Delete lending. %s", str(lending))
        except TypeError as error:
            db_session.rollback()
            logger.error("Error deleting lending. %s", error)
            raise HTTPException(
                detail={
                    "field": "lendingId",
                    "error": "Contrato de Comodato não encontrado",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            ) from error

    def get_lending_status(self, db_session: Session) -> List[LendingStatusModel]:
        """Get lending status"""
        return db_session.query(LendingStatusModel).all()
