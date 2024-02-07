"""Lenging service"""

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
    WitnessContextSchema,
    WitnessSerializerSchema,
    WorkloadSerializerSchema,
)
from src.log.services import LogService
from src.people.models import CostCenterModel, EmployeeModel
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
            signed=(
                witness.signed.strftime(DEFAULT_DATE_FORMAT) if witness.signed else None
            ),
        )

    def serialize_lending(self, lending: LendingModel) -> LendingSerializerSchema:
        """Serialize lending"""
        witnesses_serialzier = []

        for witness in lending.witnesses:
            witnesses_serialzier.append(self.serialize_witness(witness))

        asset_short = AssetShortSerializerSchema(
            asset_type=lending.asset.type.name,
            description=lending.asset.description,
            register_number=lending.asset.register_number,
        )

        return LendingSerializerSchema(
            id=lending.id,
            employee=self.serialize_employee(lending.employee),
            asset=asset_short,
            document=lending.document.id if lending.document else None,
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
            glpi_number=lending.glpi_number,
            type=lending.type.name,
            status=lending.status.name if lending.status else "",
            goal=lending.goal,
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
                db_session.query(CostCenterModel)
                .filter(CostCenterModel.id == data.cost_center_id)
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

        if data.witnesses_id:
            witnesses = []
            ids_not_found = []
            for witness in data.witnesses_id:
                witness_obj = (
                    db_session.query(WitnessModel)
                    .filter(WitnessModel.id == witness)
                    .first()
                )

                if not witness_obj:
                    employee_obj = (
                        db_session.query(EmployeeModel)
                        .filter(EmployeeModel.id == witness)
                        .first()
                    )

                    if not employee_obj:
                        ids_not_found.append(witness_obj)
                    else:
                        new_witness = WitnessModel(employee=employee)
                        db_session.add(new_witness)
                        db_session.commit()
                        db_session.flush()
                        witnesses.append(new_witness)
                else:
                    witnesses.append(witness_obj)

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
            goal=new_lending.goal,
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
            "asset",
            "Criação de Contrato de Comodato",
            new_lending_db.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Asset. %s", str(new_lending_db))

        return self.serialize_lending(new_lending_db)

    def get_lending(
        self, lending_id: int, db_session: Session
    ) -> LendingSerializerSchema:
        """Get a lending"""
        lending = self.__get_lending_or_404(lending_id, db_session)
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
            .outerjoin(CostCenterModel)
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
                    register_number=asset.register_number,
                    serial_number=asset.serial_number,
                    description=asset.description,
                    accessories=asset.accessories,
                    ms_office="SIM" if asset.ms_office else "Não",
                    pattern=asset.pattern,
                    operational_system=asset.operational_system,
                    value=str(asset.value),
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
                    goal=current_lending.goal,
                    project=current_lending.project,
                    location=current_lending.location,
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
                    register_number=asset.register_number,
                    serial_number=asset.serial_number,
                    description=asset.description,
                    accessories=asset.accessories,
                    ms_office="SIM" if asset.ms_office else "Não",
                    pattern=asset.pattern,
                    operational_system=asset.operational_system,
                    value=str(asset.value),
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
                    goal=current_lending.goal,
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
                    register_number=asset.register_number,
                    serial_number=asset.serial_number,
                    description=asset.description,
                    accessories=asset.accessories,
                    ms_office="SIM" if asset.ms_office else "Não",
                    pattern=asset.pattern,
                    operational_system=asset.operational_system,
                    value=str(asset.value),
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
                    goal=current_lending.goal,
                    project=current_lending.project,
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
                    register_number=asset.register_number,
                    serial_number=asset.serial_number,
                    description=asset.description,
                    accessories=asset.accessories,
                    ms_office="SIM" if asset.ms_office else "Não",
                    pattern=asset.pattern,
                    operational_system=asset.operational_system,
                    value=str(asset.value),
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
                    goal=current_lending.goal,
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
        current_lending.witnesses.append(witness1)
        current_lending.witnesses.append(witness2)

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
                description=asset.description,
                size=asset.clothing_size.name if asset.clothing_size else "N/A",
                quantity=asset.quantity,
                value=str(asset.value),
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
                description=asset.description,
                size=asset.clothing_size.name if asset.clothing_size else "N/A",
                quantity=asset.quantity,
                value=str(asset.value),
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
