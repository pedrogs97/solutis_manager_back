"""Lenging service"""

import locale
import logging
import os
from datetime import date
from typing import List, Union

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.asset.models import AssetModel
from src.asset.schemas import AssetShortSerializerSchema
from src.auth.models import UserModel
from src.config import BASE_DIR, CONTRACT_UPLOAD_DIR, DEBUG, DEFAULT_DATE_FORMAT
from src.datasync.models import CostCenterTOTVSModel
from src.lending.filters import DocumentFilter, LendingFilter, WorkloadFilter
from src.lending.models import (
    DocumentModel,
    DocumentTypeModel,
    LendingModel,
    LendingStatusModel,
    LendingTypeModel,
    WitnessModel,
    WorkloadModel,
)
from src.lending.schemas import (
    CostCenterSerializerSchema,
    CreateWitnessSchema,
    DocumentSerializerSchema,
    LendingSerializerSchema,
    NewLendingContextSchema,
    NewLendingDocSchema,
    NewLendingPjContextSchema,
    NewLendingSchema,
    NewLendingTermContextSchema,
    NewRevokeContractDocSchema,
    UpdateLendingSchema,
    WitnessContextSchema,
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
from src.utils import (
    create_lending_contract,
    create_lending_contract_pj,
    create_lending_term,
    create_revoke_lending_contract,
    create_revoke_lending_contract_pj,
    upload_file,
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
            workload=WorkloadSerializerSchema(**lending.workload.__dict__),
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
            type=lending.type.name,
            status=lending.status.name if lending.status else "",
            business_executive=lending.business_executive,
            project=lending.project,
            location=lending.location,
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
                    {"field": "assetId", "error": f"Ativo não existe. {asset}"}
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

        if data.type_id:
            lending_type = (
                db_session.query(LendingTypeModel)
                .filter(LendingTypeModel.id == data.type_id)
                .first()
            )
            if not lending_type:
                errors.append(
                    {
                        "field": "typeId",
                        "error": f"Tipo não existe. {lending_type}",
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
            lending_type,
        )

    def create_lending(
        self,
        new_lending: NewLendingSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ):
        """Creates new lending"""

        (
            employee,
            asset,
            workload,
            cost_center,
            witnesses,
            lending_type,
        ) = self.__validate_nested(new_lending, db_session)

        new_lending_db = LendingModel(
            manager=new_lending.manager,
            observations=new_lending.observations,
            glpi_number=new_lending.glpi_number,
            business_executive=new_lending.business_executive,
            project=new_lending.project,
            location=new_lending.location,
        )

        new_lending_db.employee = employee
        new_lending_db.asset = asset
        new_lending_db.workload = workload
        new_lending_db.cost_center = cost_center
        new_lending_db.type = lending_type

        new_lending_db.witnesses = witnesses
        db_session.add(new_lending_db)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "lending",
            "Criação de Contrato de Comodato",
            new_lending_db.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Lending. %s", str(new_lending_db))

        return self.serialize_lending(new_lending_db)

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
        db_session.add(lending)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "lending",
            f"Atualização de {lending.type.name}",
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

        lending_list = lending_filters.filter(
            db_session.query(LendingModel)
            .outerjoin(EmployeeModel)
            .outerjoin(AssetModel)
            .outerjoin(WorkloadModel)
            .outerjoin(CostCenterTOTVSModel)
            .outerjoin(LendingTypeModel)
            .outerjoin(LendingStatusModel)
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

        workloads_list = workload_filters.filter(db_session.query(WorkloadModel))

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
        )

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


class DocumentService:
    """Document service"""

    def __get_document_or_404(
        self, document_id: int, db_session: Session
    ) -> DocumentModel:
        """Get document or 404"""
        document = (
            db_session.query(DocumentModel)
            .filter(DocumentModel.id == document_id)
            .first()
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "documentId", "error": "Contrato não encontrado"},
            )

        return document

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

    def __generate_code(
        self, last_doc: Union[DocumentModel, None], asset: AssetModel
    ) -> str:
        """Generate new code for document"""
        new_code = 1

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "assetId", "error": "Ativo não encontrado"},
            )

        if last_doc:
            last_code = last_doc.id
            new_code = last_code + 1
        str_code = str(new_code)
        return asset.type.acronym + str_code.zfill(6 - len(str_code))

    def __get_term_detail(self, asset: AssetModel, cost_center: str) -> List[dict]:
        """Get asset term detail"""
        detail = []

        if not asset.type:
            return detail

        if asset.type.id == 4:
            detail.append({"key": "Modelo", "value": asset.model})
            detail.append({"key": "Marca", "value": asset.brand})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        if asset.type.id == 5:
            detail.append({"key": "IMEI", "value": asset.imei})
            detail.append({"key": "Operadora", "value": asset.operator})
            detail.append({"key": "Número Linha", "value": asset.line_number})
            detail.append({"key": "Modelo", "value": asset.model})
            detail.append({"key": "Acessórios", "value": asset.accessories})
            detail.append({"key": "Anotações", "value": asset.observations})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        if asset.type.id == 7:
            detail.append(
                {"key": "Descrição Kit Ferramentas", "value": asset.observations}
            )
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        if asset.type.id == 10:
            detail.append({"key": "Modelo", "value": asset.model})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        if asset.type.id == 11:
            detail.append({"key": "Modelo", "value": asset.model})
            detail.append({"key": "Marca", "value": asset.brand})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        if asset.type.id == 12:
            detail.append({"key": "Modelo", "value": asset.model})
            detail.append({"key": "Marca", "value": asset.brand})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        if asset.type.id == 13:
            detail.append({"key": "Modelo", "value": asset.model})
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        return detail

    def __get_contract_detail(self, asset: AssetModel) -> List[dict]:
        """Get asset contract detail"""
        detail = []

        if not asset.type:
            return detail

        if asset.type.id in (1, 2, 14, 15):
            detail.append({"key": "N° Patrimônio", "value": asset.register_number})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "Descrição", "value": asset.description})
            detail.append({"key": "Acessórios", "value": asset.accessories})
            detail.append(
                {"key": "Pacote Office", "value": "SIM" if asset.ms_office else "NÃO"}
            )
            detail.append({"key": "Padrão Equipamento", "value": asset.pattern})
            detail.append(
                {"key": "Sistema Operacional", "value": asset.operational_system}
            )
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        if asset.type.id == 3:
            detail.append({"key": "N° Patrimônio", "value": asset.register_number})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "Descrição", "value": asset.description})
            detail.append({"key": "Modelo", "value": asset.model})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        if asset.type.id == 8:
            detail.append({"key": "N° Patrimônio", "value": asset.register_number})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "Descrição", "value": asset.description})
            detail.append({"key": "Modelo", "value": asset.model})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        if asset.type.id == 9:
            detail.append({"key": "N° Patrimônio", "value": asset.register_number})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "Descrição", "value": asset.description})
            detail.append({"key": "Modelo", "value": asset.model})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": locale.currency(asset.value, grouping=True, symbol=None),
                }
            )

        return detail

    def serialize_document(self, doc: DocumentModel) -> DocumentSerializerSchema:
        """Serialize document"""
        return DocumentSerializerSchema(
            id=doc.id,
            type=doc.doc_type.name,
            path=doc.path,
            file_name=doc.file_name,
        )

    def create_contract(
        self,
        new_lending_doc: NewLendingDocSchema,
        type_doc: str,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Create new contract, not signed"""
        doc_type = (
            db_session.query(DocumentTypeModel)
            .filter(DocumentTypeModel.name == type_doc)
            .first()
        )

        lending_pending = (
            db_session.query(LendingStatusModel)
            .filter(LendingStatusModel.name == "Arquivo pendente")
            .first()
        )

        current_lending = (
            db_session.query(LendingModel)
            .filter(LendingModel.id == new_lending_doc.lending_id)
            .first()
        )

        asset = current_lending.asset

        if len(db_session.query(DocumentModel).all()):
            new_code = self.__generate_code(
                db_session.query(DocumentModel).all()[-1], asset
            )
        else:
            new_code = self.__generate_code(None, asset)

        workload = current_lending.workload

        employee = current_lending.employee

        witness1 = current_lending.witnesses[0]

        witness2 = current_lending.witnesses[1]

        detail = self.__get_contract_detail(asset)

        if new_lending_doc.legal_person:
            contract_path = create_lending_contract_pj(
                NewLendingPjContextSchema(
                    number=new_code,
                    glpi_number=(
                        current_lending.glpi_number
                        if current_lending.glpi_number
                        else ""
                    ),
                    full_name=employee.full_name,
                    taxpayer_identification=employee.taxpayer_identification,
                    national_identification=employee.national_identification,
                    address=employee.address,
                    nationality=employee.nationality.description,
                    role=employee.role.name,
                    marital_status=employee.marital_status.description,
                    cc=current_lending.cost_center.name,
                    manager=current_lending.manager,
                    business_executive=current_lending.business_executive,
                    workload=workload.name,
                    detail=detail,
                    date=date.today().strftime(DEFAULT_DATE_FORMAT),
                    witnesses=[
                        WitnessContextSchema(
                            full_name=witness1.employee.full_name,
                            taxpayer_identification=witness1.employee.taxpayer_identification,
                        ),
                        WitnessContextSchema(
                            full_name=witness2.employee.full_name,
                            taxpayer_identification=witness2.employee.taxpayer_identification,
                        ),
                    ],
                    cnpj=employee.employer_number,
                    company_address=employee.employer_address,
                    company=employee.employer_name,
                    project=current_lending.project,
                    location=current_lending.location,
                    contract_date=employee.employer_contract_date.strftime(
                        DEFAULT_DATE_FORMAT
                    ),
                )
            )
        else:
            contract_path = create_lending_contract(
                NewLendingContextSchema(
                    number=new_code,
                    glpi_number=(
                        current_lending.glpi_number
                        if current_lending.glpi_number
                        else ""
                    ),
                    full_name=employee.full_name,
                    taxpayer_identification=employee.taxpayer_identification,
                    national_identification=employee.national_identification,
                    address=employee.address,
                    nationality=employee.nationality.description,
                    role=employee.role.name,
                    marital_status=employee.marital_status.description,
                    cc=current_lending.cost_center.name,
                    manager=current_lending.manager,
                    business_executive=current_lending.business_executive,
                    workload=workload.name,
                    detail=detail,
                    date=date.today().strftime(DEFAULT_DATE_FORMAT),
                    witnesses=[
                        WitnessContextSchema(
                            full_name=witness1.employee.full_name,
                            taxpayer_identification=witness1.employee.taxpayer_identification,
                        ),
                        WitnessContextSchema(
                            full_name=witness2.employee.full_name,
                            taxpayer_identification=witness2.employee.taxpayer_identification,
                        ),
                    ],
                    cnpj=employee.employer_number,
                    company_address=employee.employer_address,
                    company=employee.employer_name,
                    project=current_lending.project,
                    location=current_lending.location,
                )
            )

        new_doc = DocumentModel(path=contract_path, file_name=f"{new_code}.pdf")

        new_doc.doc_type = doc_type

        db_session.add(new_doc)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "document",
            f"Criação de {type_doc}",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document. %s", str(new_doc))

        current_lending.document = new_doc
        current_lending.number = new_code
        current_lending.status = lending_pending

        db_session.add(current_lending)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "lending",
            "Vinculação do Contrato ao Comodato",
            current_lending.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document add to Lending. %s", str(current_lending))

        return self.serialize_document(new_doc)

    def create_revoke_contract(
        self,
        revoke_lending_doc: NewRevokeContractDocSchema,
        type_doc: str,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Create new contract, not signed"""
        doc_type = (
            db_session.query(DocumentTypeModel)
            .filter(DocumentTypeModel.name == type_doc)
            .first()
        )

        lending_pending = (
            db_session.query(LendingStatusModel)
            .filter(LendingStatusModel.name == "Arquivo de distrato pendente")
            .first()
        )

        current_lending = (
            db_session.query(LendingModel)
            .filter(LendingModel.id == revoke_lending_doc.lending_id)
            .first()
        )

        asset = current_lending.asset

        if len(db_session.query(DocumentModel).all()):
            new_code = self.__generate_code(
                db_session.query(DocumentModel).all()[-1], asset
            )
        else:
            new_code = self.__generate_code(None, asset)

        workload = current_lending.workload

        employee = current_lending.employee

        witness1 = current_lending.witnesses[0]

        witness2 = current_lending.witnesses[1]

        detail = self.__get_contract_detail(asset)

        if revoke_lending_doc.legal_person:
            contract_path = create_revoke_lending_contract_pj(
                NewLendingPjContextSchema(
                    number=new_code,
                    glpi_number=(
                        current_lending.glpi_number
                        if current_lending.glpi_number
                        else ""
                    ),
                    full_name=employee.full_name,
                    taxpayer_identification=employee.taxpayer_identification,
                    national_identification=employee.national_identification,
                    address=employee.address,
                    nationality=employee.nationality.description,
                    role=employee.role.name,
                    marital_status=employee.marital_status.description,
                    cc=current_lending.cost_center.name,
                    manager=current_lending.manager,
                    business_executive=current_lending.business_executive,
                    workload=workload.name,
                    detail=detail,
                    date=date.today().strftime(DEFAULT_DATE_FORMAT),
                    witnesses=[
                        WitnessContextSchema(
                            full_name=witness1.employee.full_name,
                            taxpayer_identification=witness1.employee.taxpayer_identification,
                        ),
                        WitnessContextSchema(
                            full_name=witness2.employee.full_name,
                            taxpayer_identification=witness2.employee.taxpayer_identification,
                        ),
                    ],
                    cnpj=employee.employer_number,
                    company_address=employee.employer_address,
                    company=employee.employer_name,
                    object=employee.employer_contract_object,
                    project=current_lending.project,
                    contract_date=employee.employer_contract_date.strftime(
                        DEFAULT_DATE_FORMAT
                    ),
                    location=current_lending.location,
                )
            )
        else:
            contract_path = create_revoke_lending_contract(
                NewLendingContextSchema(
                    number=new_code,
                    glpi_number=(
                        current_lending.glpi_number
                        if current_lending.glpi_number
                        else ""
                    ),
                    full_name=employee.full_name,
                    taxpayer_identification=employee.taxpayer_identification,
                    national_identification=employee.national_identification,
                    address=employee.address,
                    nationality=employee.nationality.description,
                    role=employee.role.name,
                    marital_status=employee.marital_status.description,
                    cc=current_lending.cost_center.name,
                    manager=current_lending.manager,
                    business_executive=current_lending.business_executive,
                    workload=workload.name,
                    detail=detail,
                    date=date.today().strftime(DEFAULT_DATE_FORMAT),
                    witnesses=[
                        WitnessContextSchema(
                            full_name=witness1.employee.full_name,
                            taxpayer_identification=witness1.employee.taxpayer_identification,
                        ),
                        WitnessContextSchema(
                            full_name=witness2.employee.full_name,
                            taxpayer_identification=witness2.employee.taxpayer_identification,
                        ),
                    ],
                    cnpj=employee.employer_number,
                    company_address=employee.employer_address,
                    company=employee.employer_name,
                    project=current_lending.project,
                    location=current_lending.location,
                )
            )

        new_doc = DocumentModel(path=contract_path, file_name=f"{new_code}.pdf")

        new_doc.doc_type = doc_type

        db_session.add(new_doc)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "document",
            f"Criação de {type_doc}",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document. %s", str(new_doc))

        current_lending.document_revoke = new_doc
        current_lending.number = new_code
        current_lending.status = lending_pending

        db_session.add(current_lending)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "lending",
            "Desvinculação do Contrato ao Comodato",
            current_lending.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document add to Lending. %s", str(current_lending))

        return self.serialize_document(new_doc)

    def create_term(
        self,
        new_lending_doc: NewLendingDocSchema,
        type_doc: str,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Create new contract, not signed"""
        doc_type = (
            db_session.query(DocumentTypeModel)
            .filter(DocumentTypeModel.name == type_doc)
            .first()
        )

        lending_pending = (
            db_session.query(LendingStatusModel)
            .filter(LendingStatusModel.name == "Arquivo pendente")
            .first()
        )

        current_lending = (
            db_session.query(LendingModel)
            .filter(LendingModel.id == new_lending_doc.lending_id)
            .first()
        )

        asset = current_lending.asset

        if len(db_session.query(DocumentModel).all()):
            new_code = self.__generate_code(
                db_session.query(DocumentModel).all()[-1], asset
            )
        else:
            new_code = self.__generate_code(None, asset)

        employee = current_lending.employee

        detail = self.__get_term_detail(asset, current_lending.cost_center.name)

        contract_path = create_lending_term(
            NewLendingTermContextSchema(
                number=new_code,
                glpi_number=(
                    current_lending.glpi_number if current_lending.glpi_number else ""
                ),
                full_name=employee.full_name,
                taxpayer_identification=employee.taxpayer_identification,
                national_identification=employee.national_identification,
                address=employee.address,
                nationality=employee.nationality.description,
                role=employee.role.name,
                cc=current_lending.cost_center.name,
                manager=current_lending.manager,
                detail=detail,
                date=date.today().strftime(DEFAULT_DATE_FORMAT),
                project=current_lending.project,
                location=current_lending.location,
            )
        )

        new_doc = DocumentModel(path=contract_path, file_name=f"{new_code}.pdf")

        new_doc.doc_type = doc_type

        db_session.add(new_doc)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "document",
            f"Criação de {type_doc}",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document. %s", str(new_doc))

        current_lending.document = new_doc
        current_lending.number = new_code
        current_lending.status = lending_pending

        db_session.add(current_lending)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "lending",
            "Vinculação do Termo",
            current_lending.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document add to Lending. %s", str(current_lending))

        return self.serialize_document(new_doc)

    def create_revoke_term(
        self,
        revoke_lending_doc: NewRevokeContractDocSchema,
        type_doc: str,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Create new contract, not signed"""
        doc_type = (
            db_session.query(DocumentTypeModel)
            .filter(DocumentTypeModel.name == type_doc)
            .first()
        )

        lending_pending = (
            db_session.query(LendingStatusModel)
            .filter(LendingStatusModel.name == "Arquivo de distrato pendente")
            .first()
        )

        current_lending = (
            db_session.query(LendingModel)
            .filter(LendingModel.id == revoke_lending_doc.lending_id)
            .first()
        )

        asset = current_lending.asset

        if len(db_session.query(DocumentModel).all()):
            new_code = self.__generate_code(
                db_session.query(DocumentModel).all()[-1], asset
            )
        else:
            new_code = self.__generate_code(None, asset)

        employee = current_lending.employee

        detail = self.__get_term_detail(asset, current_lending.cost_center.name)

        contract_path = create_lending_term(
            NewLendingTermContextSchema(
                number=new_code,
                glpi_number=(
                    current_lending.glpi_number if current_lending.glpi_number else ""
                ),
                full_name=employee.full_name,
                taxpayer_identification=employee.taxpayer_identification,
                national_identification=employee.national_identification,
                address=employee.address,
                nationality=employee.nationality.description,
                role=employee.role.name,
                cc=current_lending.cost_center.name,
                manager=current_lending.manager,
                detail=detail,
                date=date.today().strftime(DEFAULT_DATE_FORMAT),
                project=current_lending.project,
                location=current_lending.location,
            )
        )

        new_doc = DocumentModel(path=contract_path, file_name=f"{new_code}.pdf")

        new_doc.doc_type = doc_type

        db_session.add(new_doc)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "document",
            f"Criação de {type_doc}",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document. %s", str(new_doc))

        current_lending.document_revoke = new_doc
        current_lending.number = new_code
        current_lending.status = lending_pending

        db_session.add(current_lending)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "lending",
            "Vinculação do Termo",
            current_lending.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document add to Lending. %s", str(current_lending))

        return self.serialize_document(new_doc)

    async def upload_contract(
        self,
        contract: UploadFile,
        type_doc: str,
        lendingId: int,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Upload contract"""

        doc_type = (
            db_session.query(DocumentTypeModel)
            .filter(DocumentTypeModel.name == type_doc)
            .first()
        )

        lending_signed = (
            db_session.query(LendingStatusModel)
            .filter(LendingStatusModel.name == "Ativo")
            .first()
        )

        lending = self.__get_lending_or_404(lendingId, db_session)

        code = lending.number

        file_name = f"{code}.pdf"

        UPLOAD_DIR = CONTRACT_UPLOAD_DIR

        if DEBUG:
            UPLOAD_DIR = os.path.join(BASE_DIR, "storage", "contracts")

        file_path = await upload_file(
            file_name, "lending", contract.file.read(), UPLOAD_DIR
        )

        new_doc = DocumentModel(path=file_path, file_name=file_name)
        new_doc.doc_type = doc_type

        db_session.add(new_doc)
        db_session.commit()

        lending.signed_date = date.today()
        lending.document = new_doc
        lending.status = lending_signed
        db_session.add(lending)
        db_session.commit()

        service_log.set_log(
            "lending",
            "document",
            f"Importação de Contrato {type_doc}",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("Upload Document signed. %s", str(new_doc))

        return self.serialize_document(new_doc)

    async def upload_revoke_contract(
        self,
        contract: UploadFile,
        type_doc: str,
        lendingId: int,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Upload contract"""

        doc_type = (
            db_session.query(DocumentTypeModel)
            .filter(DocumentTypeModel.name == type_doc)
            .first()
        )

        lending_signed = (
            db_session.query(LendingStatusModel)
            .filter(LendingStatusModel.name == "Inativo")
            .first()
        )

        lending = self.__get_lending_or_404(lendingId, db_session)

        code = lending.number

        file_name = f"{code}.pdf"

        UPLOAD_DIR = CONTRACT_UPLOAD_DIR

        if DEBUG:
            UPLOAD_DIR = os.path.join(BASE_DIR, "storage", "contracts")

        file_path = await upload_file(
            file_name, "lending", contract.file.read(), UPLOAD_DIR
        )

        new_doc = DocumentModel(path=file_path, file_name=file_name)
        new_doc.doc_type = doc_type

        db_session.add(new_doc)
        db_session.commit()

        lending.revoke_signed_date = date.today()
        lending.document_revoke = new_doc
        lending.status = lending_signed
        db_session.add(lending)
        db_session.commit()

        service_log.set_log(
            "lending",
            "document",
            f"Importação de Distrato {type_doc}",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("Upload Document renvoke. %s", str(new_doc))

        return self.serialize_document(new_doc)

    def get_documents(
        self,
        db_session: Session,
        document_filters: DocumentFilter,
        page: int = 1,
        size: int = 50,
    ) -> Page[DocumentSerializerSchema]:
        """Get documents list"""

        document_list = document_filters.filter(
            db_session.query(DocumentModel).join(DocumentTypeModel)
        )

        params = Params(page=page, size=size)
        paginated = paginate(
            document_list,
            params=params,
            transformer=lambda document_list: [
                self.serialize_document(document).model_dump(by_alias=True)
                for document in document_list
            ],
        )
        return paginated

    def get_document(
        self, document_id: int, db_session: Session
    ) -> DocumentSerializerSchema:
        """Get a document"""

        document = self.__get_document_or_404(document_id, db_session)

        return self.serialize_document(document)
