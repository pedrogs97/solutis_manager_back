"""Lenging service"""
import logging
from datetime import date
from typing import Union

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.asset.models import AssetModel
from src.asset.schemas import AssetSerializerSchema
from src.auth.models import UserModel
from src.config import CONTRACT_UPLOAD_DIR
from src.lending.filters import LendingFilter
from src.lending.models import (
    DocumentModel,
    DocumentTypeModel,
    LendingModel,
    WitnessModel,
    WorkloadModel,
)
from src.lending.schemas import (
    CostCenterSerializerSchema,
    DocumentSerializerSchema,
    LendingSerializerSchema,
    NewLendingContextSchema,
    NewLendingDocSchema,
    NewLendingPjContextSchema,
    NewLendingSchema,
    UploadSignedContractSchema,
    WitnessContextSchema,
    WitnessSerializerSchema,
    WorkloadSerializerSchema,
)
from src.log.services import LogService
from src.people.models import CostCenterModel, EmployeeModel
from src.people.schemas import EmployeeSerializerSchema
from src.utils import create_lending_contract, create_lending_contract_pj, upload_file

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

    def serialize_lending(self, lending: LendingModel) -> LendingSerializerSchema:
        """Serialize lending"""
        witnesses_serialzier = []

        for witness in lending.witnesses:
            witnesses_serialzier.append(
                WitnessSerializerSchema(
                    id=witness.id,
                    employee=EmployeeSerializerSchema(**witness.employee.__dict__),
                    signed=witness.signed.strftime("DEFAULT_DATE_FORMAT"),
                )
            )

        return LendingSerializerSchema(
            id=lending.id,
            employee=EmployeeSerializerSchema(**lending.employee.__dict__),
            asset=AssetSerializerSchema(**lending.asset.__dict__),
            document=lending.document.id,
            workload=WorkloadSerializerSchema(**lending.workload.__dict__),
            witnesses=witnesses_serialzier,
            cost_center=CostCenterSerializerSchema(**lending.cost_center.__dict__),
            manager=lending.manager,
            observations=lending.observations,
            signed_date=lending.signed_date.strftime("DEFAULT_DATE_FORMAT"),
            glpi_number=lending.glpi_number,
        )

    def __validate_nested(self, data: NewLendingSchema, db_session: Session) -> tuple:
        """Validates employee, asset, workload, cost center and document values"""
        errors = {}
        if data.employee:
            employee = (
                db_session.query(EmployeeModel)
                .filter(EmployeeModel.id == data.employee)
                .first()
            )
            if not employee:
                errors.update(
                    {
                        "field": "employeeId",
                        "error": f"Tipo de Colaborador não existe. {employee}",
                    }
                )

        if data.asset:
            asset = (
                db_session.query(AssetModel).filter(AssetModel.id == data.asset).first()
            )
            if not asset:
                errors.update(
                    {"field": "assetId", "error": f"Ativo não existe. {asset}"}
                )

        if data.document:
            document = (
                db_session.query(DocumentModel)
                .filter(DocumentModel.id == data.document)
                .first()
            )
            if not document:
                errors.update(
                    {
                        "field": "documentId",
                        "error": f"Documento não existe. {document}",
                    }
                )

        if data.workload:
            workload = (
                db_session.query(WorkloadModel)
                .filter(WorkloadModel.id == data.workload)
                .first()
            )
            if not workload:
                errors.update(
                    {"field": "workloadId", "error": f"Lotação não existe. {workload}"}
                )

        if data.cost_center:
            cost_center = (
                db_session.query(CostCenterModel)
                .filter(CostCenterModel.id == data.cost_center)
                .first()
            )
            if not cost_center:
                errors.update(
                    {
                        "field": "costCenter",
                        "error": f"Centro de Custo não existe. {cost_center}",
                    }
                )

        if data.witnesses:
            witnesses = []
            ids_not_found = []
            for witness in data.witnesses:
                witness_obj = (
                    db_session.query(WitnessModel)
                    .filter(WitnessModel.id == witness)
                    .first()
                )
                if not witness_obj:
                    ids_not_found.append(witness_obj)
                witnesses.append(witness)
            errors.update(
                {
                    "field": "witnessId",
                    "error": {"Testemunhas não encontradas": ids_not_found},
                }
            )

        if len(errors.keys()) > 0:
            raise HTTPException(
                detail=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return (
            employee,
            asset,
            document,
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

        (
            employee,
            asset,
            document,
            workload,
            cost_center,
            witnesses,
        ) = self.__validate_nested(new_lending, db_session)

        new_lending_db = LendingModel(
            manager=new_lending.manager,
            observations=new_lending.observations,
            signed_date=new_lending.signed_date,
            glpi_number=new_lending.glpi_number,
        )

        new_lending_db.employee = employee
        new_lending_db.asset = asset
        new_lending_db.document = document
        new_lending_db.workload = workload
        new_lending_db.cost_center = cost_center

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
    ) -> AssetSerializerSchema:
        """Get a lending"""
        lending = self.__get_lending_or_404(lending_id, db_session)
        return self.serialize_lending(lending)

    def get_lendings(
        self,
        db_session: Session,
        lending_filters: LendingFilter,
        page: int = 1,
        size: int = 50,
    ) -> Page[AssetSerializerSchema]:
        """Get lendings list"""

        lending_list = lending_filters.filter(db_session.query(LendingModel))

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

        asset = (
            db_session.query(AssetModel)
            .filter(AssetModel.id == new_lending_doc.asset_id)
            .first()
        )

        new_code = self.__generate_code(
            db_session.query(DocumentModel).all()[-1], asset
        )

        current_lending = (
            db_session.query(LendingModel)
            .filter(LendingModel.id == new_lending_doc.lending_id)
            .first()
        )

        workload = (
            db_session.query(WorkloadModel)
            .filter(WorkloadModel.id == new_lending_doc.workload_id)
            .first()
        )

        employee = (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.id == new_lending_doc.employee_id)
            .first()
        )

        witness1 = (
            db_session.query(WitnessModel)
            .filter(WitnessModel.id == new_lending_doc.witness1_id)
            .first()
        )

        witness2 = (
            db_session.query(WitnessModel)
            .filter(WitnessModel.id == new_lending_doc.witness2_id)
            .first()
        )

        if new_lending_doc.legal_person:
            contract_path = create_lending_contract_pj(
                NewLendingPjContextSchema(
                    number=new_code,
                    glpi_number=new_lending_doc.glpi_number,
                    full_name=employee.full_name,
                    taxpayer_identification=employee.taxpayer_identification,
                    national_identification=employee.national_identification,
                    address=employee.address,
                    nationality=employee.nationality.description,
                    role=employee.role.name,
                    marital_status=employee.marital_status.description,
                    cc=new_lending_doc.cc,
                    manager=new_lending_doc.manager,
                    business_executive=new_lending_doc.business_executive,
                    workload=workload.name,
                    register_number=asset.register_number,
                    serial_number=asset.serial_number,
                    description=asset.description,
                    accessories=asset.accessories,
                    ms_office="SIM" if asset.ms_office else "Não",
                    pattern=asset.pattern,
                    operational_system=asset.operational_system,
                    value=asset.value,
                    date=date.today().strftime("DEFAULT_DATE_FORMAT"),
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
                    date_confirm=new_lending_doc.date_confirm,
                    goal=new_lending_doc.goal,
                    project=new_lending_doc.project,
                )
            )
        else:
            contract_path = create_lending_contract(
                NewLendingContextSchema(
                    number=new_code,
                    glpi_number=new_lending_doc.glpi_number,
                    full_name=employee.full_name,
                    taxpayer_identification=employee.taxpayer_identification,
                    national_identification=employee.national_identification,
                    address=employee.address,
                    nationality=employee.nationality.description,
                    role=employee.role.name,
                    marital_status=employee.marital_status.description,
                    cc=new_lending_doc.cc,
                    manager=new_lending_doc.manager,
                    business_executive=new_lending_doc.business_executive,
                    workload=workload.name,
                    register_number=asset.register_number,
                    serial_number=asset.serial_number,
                    description=asset.description,
                    accessories=asset.accessories,
                    ms_office="SIM" if asset.ms_office else "Não",
                    pattern=asset.pattern,
                    operational_system=asset.operational_system,
                    value=asset.value,
                    date=date.today().strftime("DEFAULT_DATE_FORMAT"),
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
            "Criação de Contrato",
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
            "Vinculação do Contrato ao Comodato",
            current_lending.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document add to Lending. %s", str(current_lending))

        return self.serialize_document(new_doc)

    async def upload_contract(
        self,
        contract: UploadFile,
        data: UploadSignedContractSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Upload contract"""

        lending = self.__get_lending_or_404(data.lending_id, db_session)
        document = self.__get_document_or_404(data.document_id, db_session)

        code = lending.number

        file_name = f"{code}.pdf"
        file_path = await upload_file(
            file_name, "lending", contract.file.read(), CONTRACT_UPLOAD_DIR
        )

        document.path = file_path
        document.file_name = file_name

        db_session.add(document)
        db_session.commit()

        lending.signed_date = date.today()

        db_session.add(lending)
        db_session.commit()

        service_log.set_log(
            "lending",
            "document",
            "Importação de Contrato de Comodato",
            document.id,
            authenticated_user,
            db_session,
        )
        logger.info("Upload Document signed. %s", str(document))

        return self.serialize_document(document)
