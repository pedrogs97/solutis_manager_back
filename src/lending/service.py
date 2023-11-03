"""Lenging service"""
import logging
from datetime import date
from typing import List, Union

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.lending.models import (AssetClothingSizeModel, AssetModel,
                                AssetStatusModel, AssetTypeModel,
                                CostCenterModel, DocumentModel,
                                DocumentTypeModel, LendingModel,
                                VerificationAnswerModel, VerificationModel,
                                VerificationTypeModel, WitnessModel,
                                WorkloadModel)
from src.lending.schemas import (AssetClothingSizeSerializer,
                                 AssetSerializerSchema,
                                 AssetStatusSerializerSchema, AssetTotvsSchema,
                                 AssetTypeSerializerSchema,
                                 AssetTypeTotvsSchema,
                                 CostCenterSerializerSchema,
                                 CostCenterTotvsSchema,
                                 DocumentSerializerSchema,
                                 InactivateAssetSchema,
                                 LendingSerializerSchema, NewAssetSchema,
                                 NewLendingContextSchema, NewLendingDocSchema,
                                 NewLendingPjContextSchema, NewLendingSchema,
                                 NewVerificationAnswerSchema,
                                 NewVerificationSchema, UpdateAssetSchema,
                                 UploadSignedContractSchema,
                                 VerificationAnswerSerializerSchema,
                                 VerificationSerializerSchema,
                                 WitnessContextSchema, WitnessSerializerSchema,
                                 WorkloadSerializerSchema)
from src.log.services import LogService
from src.people.models import EmployeeModel
from src.people.schemas import EmployeeSerializerSchema
from src.utils import (create_lending_contract, create_lending_contract_pj,
                       upload_file)

logger = logging.getLogger(__name__)
service_log = LogService()


class AssetService():
    """Asset services"""

    def __get_asset_or_404(self, asset_id: int, db_session: Session) -> AssetModel:
        """Get asset or 404"""
        asset = db_session.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ativo não encontrado"
            )

        return asset

    def __validate_nested(self, data: NewAssetSchema, db_session: Session) -> tuple:
        """Validates clothing size, type and status values"""
        if data.type:
            asset_type = (
                db_session.query(AssetTypeModel)
                .filter(AssetTypeModel.name == data.type)
                .first()
            )
            if not asset_type:
                raise HTTPException(
                    detail=f"Tipo de Ativo não existe. {asset_type}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.clothing_size:
            clothing_size = (
                db_session.query(AssetClothingSizeModel)
                .filter(AssetClothingSizeModel.name == data.clothing_size)
                .first()
            )
            if not clothing_size:
                raise HTTPException(
                    detail=f"Tamanho de roupa não existe. {clothing_size}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.status:
            asset_status = (
                db_session.query(AssetStatusModel)
                .filter(AssetStatusModel.name == data.status)
                .first()
            )
            if not asset_status:
                raise HTTPException(
                    detail=f"Situação de Ativo não existe. {asset_status}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        return (
            asset_type,
            clothing_size,
            asset_status,
        )

    def serialize_asset(self, asset: AssetModel) -> AssetSerializerSchema:
        """Serialize asset"""
        return AssetSerializerSchema(
            id=asset.id,
            type=AssetTypeSerializerSchema(**asset.type.__dict__),
            clothing_size=AssetClothingSizeSerializer(**asset.clothing_size.__dict__),
            status=AssetStatusSerializerSchema(**asset.status),
            register_number=asset.register_number,
            description=asset.description,
            supplier=asset.supplier,
            assurance_date=asset.assurance_date,
            observations=asset.observations,
            discard_reason=asset.discard_reason,
            pattern=asset.pattern,
            operational_system=asset.operational_system,
            serial_number=asset.serial_number,
            imei=asset.imei,
            acquisition_date=asset.acquisition_date,
            value=asset.value,
            ms_office=asset.ms_office,
            line_number=asset.line_number,
            operator=asset.operator,
            model=asset.model,
            accessories=asset.accessories,
            configuration=asset.configuration,
            quantity=asset.quantity,
            unit=asset.unit,
        )

    def create_asset(
        self, data: NewAssetSchema, db_session: Session, authenticated_user: UserModel
    ) -> AssetSerializerSchema:
        """Creates new asset"""
        if (
            data.code
            and db_session.query(AssetModel)
            .filter(AssetModel.code == data.code)
            .first()
        ):
            raise HTTPException(
                detail="Este Código já existe.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if (
            db_session.query(AssetModel)
            .filter(AssetModel.register_number == data.register_number)
            .first()
        ):
            raise HTTPException(
                detail="Este N° de Patrimônio já existe",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        (
            asset_type,
            clothing_size,
            asset_status,
        ) = self.__validate_nested(data, db_session)

        new_asset = AssetModel(
            type=asset_type,
            clothing_size=clothing_size,
            status=asset_status,
            code=data.code,
            register_number=data.register_number,
            description=data.description,
            supplier=data.supplier,
            assurance_date=data.assurance_date,
            observations=data.observations,
            discard_reason=data.discard_reason,
            pattern=data.pattern,
            operational_system=data.operational_system,
            serial_number=data.serial_number,
            imei=data.imei,
            acquisition_date=data.acquisition_date,
            value=data.value,
            ms_office=data.ms_office,
            line_number=data.line_number,
            operator=data.operator,
            model=data.model,
            accessories=data.accessories,
            configuration=data.configuration,
            quantity=data.quantity,
            unit=data.unit,
            active=True,
            by_agile=True,
        )
        db_session.add(new_asset)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending", "asset", "Criação de Ativo", new_asset.id, authenticated_user
        )
        logger.info("New Asset. %s", str(new_asset))

        return self.serialize_asset(new_asset)

    def update_asset(
        self,
        asset_id: int,
        data: UpdateAssetSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> AssetSerializerSchema:
        """Uptades an asset"""
        asset = self.__get_asset_or_404(asset_id, db_session)

        if data.observations:
            asset.observations = data.observations

        db_session.add(asset)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending", "asset", "Edição de Ativo", asset.id, authenticated_user
        )
        logger.info("Updated Asset. %s", str(asset))
        return self.serialize_asset(asset)

    def inactivate_asset(
        self,
        asset_id: int,
        data: InactivateAssetSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> AssetSerializerSchema:
        """Uptades an asset"""
        asset = self.__get_asset_or_404(asset_id, db_session)

        if data.active:
            asset.active = data.active

        db_session.add(asset)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending", "asset", "Inativação de Ativo", asset.id, authenticated_user
        )
        logger.info("Inactivate Asset. %s", str(asset))
        return self.serialize_asset(asset)

    def get_asset(self, asset_id: int, db_session: Session) -> AssetSerializerSchema:
        """Get an asset"""
        asset = self.__get_asset_or_404(asset_id, db_session)
        return self.serialize_asset(asset)

    def get_assets(
        self,
        db_session: Session,
        search: str = "",
        filter_asset: str = None,
        active: bool = True,
        page: int = 1,
        size: int = 50,
    ) -> Page[AssetSerializerSchema]:
        """Get assets list"""

        asset_list = db_session.query(AssetModel).filter(
            or_(
                AssetModel.code.ilike(f"%{search}"),
                AssetModel.register_number.ilike(f"%{search}%"),
                AssetModel.description.ilike(f"%{search}"),
                AssetModel.supplier.ilike(f"%{search}"),
                AssetModel.pattern.ilike(f"%{search}"),
                AssetModel.operational_system.ilike(f"%{search}"),
                AssetModel.serial_number.ilike(f"%{search}"),
                AssetModel.imei.ilike(f"%{search}"),
                AssetModel.line_number.ilike(f"%{search}"),
                AssetModel.operator.ilike(f"%{search}"),
                AssetModel.model.ilike(f"%{search}"),
            )
        )

        if filter_asset:
            asset_list = asset_list.join(
                AssetModel.type,
            ).filter(
                or_(
                    AssetTypeModel.name == filter_asset,
                )
            )

            asset_list = asset_list.join(
                AssetModel.status,
            ).filter(
                or_(
                    AssetStatusModel.name == filter_asset,
                )
            )

            asset_list = asset_list.join(
                AssetModel.clothing_size,
            ).filter(
                or_(
                    AssetClothingSizeModel.name == filter_asset,
                )
            )

        asset_list = asset_list.filter(AssetModel.active == active)

        params = Params(page=page, size=size)
        paginated = paginate(
            asset_list,
            params=params,
            transformer=lambda asset_list: [
                self.serialize_asset(asset) for asset in asset_list
            ],
        )
        return paginated

    def update_asset_totvs(
        self, totvs_assets: List[AssetTotvsSchema], db_session: Session
    ):
        """Updates assets from totvs"""
        try:
            updates: List[AssetModel] = []
            for totvs_asset in totvs_assets:
                if (
                    db_session.query(AssetModel)
                    .filter(AssetModel.code == totvs_asset.code)
                    .first()
                ):
                    continue

                asset_type = (
                    db_session.query(AssetTypeModel)
                    .filter(AssetTypeModel.name == totvs_asset.type)
                    .first()
                )

                dict_asset = {
                    **totvs_asset.model_dump(exclude={"asset_type"}),
                    "type": asset_type,
                }

                updates.append(AssetModel(**dict_asset))

            db_session.add_all(updates)
            db_session.commit()
            logger.info("Update Assets from TOTVS. Total=%s", str(len(updates)))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc

    def update_asset_type_totvs(
        self,
        totvs_asset_type: List[AssetTypeTotvsSchema],
        db_session: Session,
    ):
        """Updates asset type from totvs"""
        try:
            updates: List[AssetTypeModel] = []
            for totvs_asset_type_item in totvs_asset_type:
                db_asset_type = (
                    db_session.query(AssetTypeModel)
                    .filter(AssetTypeModel.code == totvs_asset_type_item.code)
                    .first()
                )
                if db_asset_type:
                    db_asset_type.group_code = totvs_asset_type_item.group_code
                    db_asset_type.name = totvs_asset_type_item.name
                    updates.append(db_asset_type)
                    continue

                updates.append(
                    AssetTypeModel(
                        **totvs_asset_type_item.model_dump(),
                        acronym=totvs_asset_type_item.name[:2].upper(),
                    )
                )

            db_session.add_all(updates)
            db_session.commit()
            logger.info("Update Asset Types from TOTVS. Total=%s", str(len(updates)))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc

    def update_cost_center_totvs(
        self,
        totvs_cost_center: List[CostCenterTotvsSchema],
        db_session: Session,
    ):
        """Updates asset type from totvs"""
        try:
            updates: List[CostCenterModel] = []
            for totvs_cost_center_item in totvs_cost_center:
                db_cost_center = (
                    db_session.query(CostCenterModel)
                    .filter(CostCenterModel.code == totvs_cost_center_item.code)
                    .first()
                )
                if db_cost_center:
                    db_cost_center.code = totvs_cost_center_item.code
                    db_cost_center.classification = (
                        totvs_cost_center_item.classification
                    )
                    db_cost_center.name = totvs_cost_center_item.name
                    updates.append(db_cost_center)
                    continue

                updates.append(CostCenterModel(**totvs_cost_center_item.model_dump()))

            db_session.add_all(updates)
            db_session.commit()
            logger.info("Update Cost Centers from TOTVS. Total=%s", str(len(updates)))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc


class LendingService():
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
                detail="Contrato de Comodato não encontrado",
            )

        return lending

    def serialize_lending(self, lending: LendingModel) -> LendingSerializerSchema:
        """Serialize lending"""
        witnesses_serialzier = []

        for witness in lending.witnesses:
            witnesses_serialzier.append(
                WitnessSerializerSchema(
                    id=witness.id,
                    employee=EmployeeSerializerSchema(**witness.employee),
                    signed=witness.signed.strftime("%d/%m/%Y"),
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
            signed_date=lending.signed_date.strftime("%d/%m/%Y"),
            glpi_number=lending.glpi_number,
        )

    def __validate_nested(self, data: NewLendingSchema, db_session: Session) -> tuple:
        """Validates employee, asset, workload, cost center and document values"""
        if data.employee:
            employee = (
                db_session.query(EmployeeModel)
                .filter(EmployeeModel.id == data.employee)
                .first()
            )
            if not employee:
                raise HTTPException(
                    detail=f"Tipo de Colaborador não existe. {employee}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.asset:
            asset = (
                db_session.query(AssetModel).filter(AssetModel.id == data.asset).first()
            )
            if not asset:
                raise HTTPException(
                    detail=f"Ativo não existe. {asset}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.document:
            document = (
                db_session.query(DocumentModel)
                .filter(DocumentModel.id == data.document)
                .first()
            )
            if not document:
                raise HTTPException(
                    detail=f"Documento não existe. {document}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.workload:
            workload = (
                db_session.query(WorkloadModel)
                .filter(WorkloadModel.id == data.workload)
                .first()
            )
            if not workload:
                raise HTTPException(
                    detail=f"Lotação não existe. {workload}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.cost_center:
            cost_center = (
                db_session.query(CostCenterModel)
                .filter(CostCenterModel.id == data.cost_center)
                .first()
            )
            if not cost_center:
                raise HTTPException(
                    detail=f"Centro de Custo não existe. {cost_center}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.witnesses:
            witnesses = []
            for witness in data.witnesses:
                witiness = (
                    db_session.query(WitnessModel)
                    .filter(WitnessModel.id == witness)
                    .first()
                )
                if not witiness:
                    raise HTTPException(
                        detail=f"Testemunha não existe. {witiness}",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
                witnesses.append(witness)

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
            employee=employee,
            asset=asset,
            document=document,
            workload=workload,
            cost_center=cost_center,
            manager=new_lending.manager,
            observations=new_lending.observations,
            signed_date=new_lending.signed_date,
            glpi_number=new_lending.glpi_number,
        )

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
        )
        logger.info("New Asset. %s", str(new_lending_db))

        return self.serialize_lending(new_lending_db)

    def get_lending(self, lending_id: int, db_session: Session) -> AssetSerializerSchema:
        """Get a lending"""
        lending = self.__get_lending_or_404(lending_id, db_session)
        return self.serialize_lending(lending)

    def get_lendings(
        self,
        db_session: Session,
        search: str = "",
        filter_lending: str = None,
        page: int = 1,
        size: int = 50,
    ) -> Page[AssetSerializerSchema]:
        """Get lendings list"""

        lending_list = (
            db_session.query(LendingModel)
            .join(
                LendingModel.employee,
            )
            .filter(
                or_(
                    LendingModel.glpi_number.ilike(f"%{search}"),
                    LendingModel.manager.ilike(f"%{search}%"),
                    EmployeeModel.full_name == filter_lending,
                )
            )
        )

        if filter_lending:
            lending_list = lending_list.filter(
                LendingModel.signed_date == filter_lending,
            )

            lending_list = lending_list.join(
                LendingModel.asset,
            ).filter(
                or_(
                    AssetModel.code == filter_lending,
                    AssetModel.description == filter_lending,
                    AssetModel.register_number == filter_lending,
                    AssetModel.serial_number == filter_lending,
                )
            )

            lending_list = lending_list.join(
                LendingModel.workload,
            ).filter(
                or_(
                    WorkloadModel.name == filter_lending,
                )
            )

        params = Params(page=page, size=size)
        paginated = paginate(
            lending_list,
            params=params,
            transformer=lambda lending_list: [
                self.serialize_lending(lending) for lending in lending_list
            ],
        )
        return paginated


class DocumentService():
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
                detail="Contrato de Comodato não encontrado",
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
                detail="Contrato de Comodato não encontrado",
            )

        return lending

    def __generate_code(
        self, last_doc: Union[DocumentModel, None], asset: AssetModel
    ) -> str:
        """Generate new code for document"""
        new_code = 1

        if not asset:
            raise HTTPException(404, "Ativo não encontrado")

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
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Create new contract, not signed"""
        doc_type = db_session.query(DocumentTypeModel).filter(
            DocumentTypeModel.name == new_lending_doc.type_doc
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
                    nacional_identification=employee.nacional_identification,
                    address=employee.address,
                    nationality=employee.nationality.description,
                    role=employee.role.name,
                    matrimonial_status=employee.matrimonial_status.description,
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
                    date=date.today().strftime("%d/%m/%Y"),
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
                    nacional_identification=employee.nacional_identification,
                    address=employee.address,
                    nationality=employee.nationality.description,
                    role=employee.role.name,
                    matrimonial_status=employee.matrimonial_status.description,
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
                    date=date.today().strftime("%d/%m/%Y"),
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

        new_doc = DocumentModel(
            doc_type=doc_type, path=contract_path, file_name=f"{new_code}.pdf"
        )

        db_session.add(new_doc)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "document",
            "Criação de Contrato de Comodato",
            new_doc.id,
            authenticated_user,
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
            "Criação de Contrato de Comodato",
            current_lending.id,
            authenticated_user,
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
        file_path = await upload_file(file_name, "lending", contract.file.read())

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
        )
        logger.info("Upload Document signed. %s", str(document))

        return self.serialize_document(document)


class VerificationService():
    """Verification service"""

    def __get_verification_or_404(
        self, verification_id: int, db_session: Session
    ) -> VerificationModel:
        """Get verification or 404"""
        document = (
            db_session.query(VerificationModel)
            .filter(VerificationModel.id == verification_id)
            .first()
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pergunta de Verificação não encontrada."         
            )

        return document
    
    def __get_asset_type_or_404(
        self, asset_type_id: int, db_session: Session
    ) -> AssetTypeModel:
        """Get asset type or 404"""
        asset_type = db_session.query(AssetTypeModel).filter(AssetTypeModel.id == asset_type_id).first()

        if not asset_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tipo do Ativo não encontrado."        
            )
        return asset_type

    def __get_verification_type_or_404(
        self, verification_type_id: int, db_session: Session
    ) -> VerificationTypeModel:
        """Get verification type or 404"""
        vertification_type = db_session.query(VerificationTypeModel).filter(VerificationTypeModel.id == verification_type_id).first()

        if not vertification_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tipo do Verificação não encontrado."        
            )
        return vertification_type
    
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
                detail="Contrato de Comodato não encontrado",
            )

        return lending

    def serialize_verification(self, verification: VerificationModel) -> VerificationSerializerSchema:
        """Serialize verification"""
        return VerificationSerializerSchema(
            id=verification.id,
            question=verification.question,
            step=verification.step,
        )
    
    def serialize_answer_verification(self, answer_verification: VerificationAnswerModel) -> VerificationAnswerSerializerSchema:
        """Serialize answer verification"""
        return VerificationAnswerSerializerSchema(
            id=answer_verification.id,
            type=answer_verification.type.name,
            answer=answer_verification.answer,
            lending_id=answer_verification.lending.id,
            verification=self.serialize_verification(answer_verification.verification)
        )


    def create_verification(self, data: NewVerificationSchema, db_session: Session, authenticated_user: UserModel) -> VerificationSerializerSchema:
        """Creates new asset verification"""

        asset_type = self.__get_asset_type_or_404(data.asset_type_id, db_session)
        
        new_verification = VerificationModel(
            question=data.question,
            asset_type=asset_type,
            step=data.step,
        )

        db_session.add(new_verification)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "verification",
            f"Adição de nova pergunta de verificação para {str(asset_type)}",
            new_verification.id,
            authenticated_user,
        )
        logger.info("New verification. %s", str(new_verification))

        return self.serialize_verification(new_verification)
    
    def get_asset_verifications(self, asset_type_id: int, db_session: Session) -> List[VerificationSerializerSchema]:
        """Returns asset type verifications"""        
        verifications = db_session.query(VerificationModel).filter(VerificationModel.asset_type_id == asset_type_id).all()

        return [VerificationSerializerSchema(
            id=verification.id,
            question=verification.question,
            asset_type=verification.asset_type.name,
        ) for verification in verifications]
    
    def create_answer_verification(self, data: NewVerificationAnswerSchema, db_session: Session, authenticated_user: UserModel) -> VerificationAnswerSerializerSchema:
        """Creates new answer verification"""

        verification = self.__get_verification_or_404(data.verification_id, db_session)

        verification_type = self.__get_verification_type_or_404(data.type_id, db_session)

        lending = self.__get_lending_or_404(data.lending_id, db_session)
        
        new_answer_verification = VerificationAnswerModel(
            lending=lending,
            verification=verification,
            type=verification_type,
            step=data.step,
            answer=data.answer,
            observations=data.observations,
        )

        db_session.add(new_answer_verification)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "verification",
            f"Adição de nova  resposta verificação",
            new_answer_verification.id,
            authenticated_user,
        )
        logger.info("New answer verification. %s", str(new_answer_verification))

        return self.serialize_answer_verification(new_answer_verification)
