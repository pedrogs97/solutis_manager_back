"""Lenging service"""

import locale
import os
from datetime import date
from typing import Dict, List, Optional, Union

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from pydantic import ValidationError
from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.asset.enums import AssetStatusEnum
from src.asset.models import AssetModel, AssetStatusModel
from src.asset.service import AssetService
from src.auth.models import UserModel
from src.clicksign_api.service import ClickSignService
from src.config import (BASE_DIR, CONTRACT_UPLOAD_DIR, DEBUG,
                        DEFAULT_DATE_FORMAT)
from src.document.enums import DocumentTypeEnum
from src.document.filters import DocumentFilter
from src.document.models import DocumentModel, DocumentTypeModel
from src.document.schemas import (DocumentSerializerSchema,
                                  NewLendingContextSchema, NewLendingDocSchema,
                                  NewLendingPjContextSchema,
                                  NewRevokeContractDocSchema,
                                  NewRevokeTermDocSchema, NewTermContextSchema,
                                  NewTermDocSchema, RecrateLendingDocSchema,
                                  VerificationContextSchema,
                                  WitnessContextSchema)
from src.lending.models import (LendingAttachments, LendingModel,
                                LendingStatusModel, WitnessModel)
from src.log.services import LogService
from src.people.models import EmployeeModel
from src.term.models import TermItemModel, TermModel, TermStatusModel
from src.utils import (create_lending_contract, create_lending_contract_pj,
                       create_revoke_lending_contract,
                       create_revoke_lending_contract_pj, create_term,
                       create_verification_document, get_image_to_pdf,
                       upload_file)
from src.verification.models import VerificationAnswerModel

service_log = LogService()
locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")


class DocumentService:
    """Document service"""

    NOT_PROVIDE = "Não informado"
    clicksign_service = ClickSignService()

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
            db_session.close()
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
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "lendingId",
                    "error": "Contrato de Comodato não encontrado",
                },
            )

        return lending

    def __get_term_or_404(self, term_id: int, db_session: Session) -> TermModel:
        """Get term or 404"""
        term = db_session.query(TermModel).filter(TermModel.id == term_id).first()
        if not term:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "termId",
                    "error": "Termo de Responsabilidade não encontrado",
                },
            )

        return term

    def __generate_code(
        self,
        last_doc: Union[DocumentModel, None],
        asset: Optional[AssetModel] = None,
        type_code="lending",
    ) -> str:
        """Generate new code for document"""
        new_code = 1

        if not asset and type_code == "lending":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "assetId", "error": "Ativo não encontrado"},
            )

        if last_doc:
            last_code = last_doc.id
            new_code = last_code + 1
        str_code = str(new_code)

        if type_code == "lending":
            asset_type = getattr(asset, "type", None)
            if asset_type and getattr(asset_type, "acronym", None):
                acronym = asset_type.acronym
            else:
                description = getattr(asset, "description", None) or ""
                if not description:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "field": "assetId",
                            "error": (
                                "Ativo sem sigla de tipo e sem descrição para gerar código."
                            ),
                        },
                    )
                acronym = description[:3]
        else:
            acronym = ""

        return acronym + str_code.zfill(6 - len(str_code))

    def __get_term_detail(self, item: TermItemModel, item_type: str) -> List[dict]:
        """Get asset term detail"""
        detail = []

        if item_type == "Kit Ferramenta":
            detail.append(
                {
                    "key": "Descrição Kit Ferramentas",
                    "value": item.description,
                }
            )

        if item_type == "Fardamento":
            detail.append(
                {
                    "key": "Descrição",
                    "value": item.description,
                },
            )
            detail.append(
                {
                    "key": "Tamanho",
                    "value": item.size,
                },
            )
            detail.append(
                {
                    "key": "Quantidade",
                    "value": item.quantity,
                },
            )
            detail.append(
                {
                    "key": "Valor",
                    "value": item.value,
                },
            )

        if item_type == "Chip":
            detail.append(
                {
                    "key": "Descrição",
                    "value": item.description,
                },
            )
            detail.append(
                {
                    "key": "Linha telefônica",
                    "value": item.line_number,
                },
            )
            detail.append(
                {
                    "key": "Operadora",
                    "value": item.operator,
                },
            )

        return detail

    def __get_contract_detail(
        self, asset: AssetModel, cost_center: str, ms_office: bool
    ) -> List[dict]:
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
                {"key": "Pacote Office", "value": "SIM" if ms_office else "NÃO"}
            )
            detail.append(
                {
                    "key": "Padrão Equipamento",
                    "value": asset.pattern if asset.pattern else self.NOT_PROVIDE,
                }
            )
            detail.append(
                {
                    "key": "Sistema Operacional",
                    "value": (
                        asset.operational_system
                        if asset.operational_system
                        else self.NOT_PROVIDE
                    ),
                }
            )
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 3:
            detail.append({"key": "N° Patrimônio", "value": asset.register_number})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "Descrição", "value": asset.description})
            detail.append(
                {
                    "key": "Modelo",
                    "value": asset.model if asset.model else self.NOT_PROVIDE,
                }
            )
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 8:
            detail.append({"key": "N° Patrimônio", "value": asset.register_number})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "Descrição", "value": asset.description})
            detail.append(
                {
                    "key": "Modelo",
                    "value": asset.model if asset.model else self.NOT_PROVIDE,
                }
            )
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 9:
            detail.append({"key": "N° Patrimônio", "value": asset.register_number})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "Descrição", "value": asset.description})
            detail.append(
                {
                    "key": "Modelo",
                    "value": asset.model if asset.model else self.NOT_PROVIDE,
                }
            )
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 4:
            detail.append(
                {
                    "key": "Modelo",
                    "value": asset.model if asset.model else self.NOT_PROVIDE,
                }
            )
            detail.append(
                {
                    "key": "Marca",
                    "value": asset.brand if asset.brand else self.NOT_PROVIDE,
                }
            )
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 5:
            detail.append({"key": "IMEI", "value": asset.imei})
            detail.append({"key": "Operadora", "value": asset.operator})
            detail.append({"key": "Número Linha", "value": asset.line_number})
            detail.append(
                {
                    "key": "Modelo",
                    "value": asset.model if asset.model else self.NOT_PROVIDE,
                }
            )
            detail.append({"key": "Acessórios", "value": asset.accessories})
            detail.append({"key": "Anotações", "value": asset.observations})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 7:
            detail.append(
                {"key": "Descrição Kit Ferramentas", "value": asset.observations}
            )
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 10:
            detail.append(
                {
                    "key": "Modelo",
                    "value": asset.model if asset.model else self.NOT_PROVIDE,
                }
            )
            detail.append({"key": "Descrição", "value": asset.description})
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 11:
            detail.append(
                {
                    "key": "Modelo",
                    "value": asset.model if asset.model else self.NOT_PROVIDE,
                }
            )
            detail.append(
                {
                    "key": "Marca",
                    "value": asset.brand if asset.brand else self.NOT_PROVIDE,
                }
            )
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 12:
            detail.append(
                {
                    "key": "Modelo",
                    "value": asset.model if asset.model else self.NOT_PROVIDE,
                }
            )
            detail.append(
                {
                    "key": "Marca",
                    "value": asset.brand if asset.brand else self.NOT_PROVIDE,
                }
            )
            detail.append({"key": "Número de Série", "value": asset.serial_number})
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 13:
            detail.append(
                {
                    "key": "Modelo",
                    "value": asset.model if asset.model else self.NOT_PROVIDE,
                }
            )
            detail.append({"key": "C.C.", "value": cost_center})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        if asset.type.id == 16:
            detail.append({"key": "N° Patrimônio", "value": asset.register_number})
            detail.append({"key": "Descrição", "value": asset.description})
            detail.append(
                {
                    "key": "Valor R$",
                    "value": self.__format_currency_value(asset.value),
                }
            )

        return detail

    def __format_currency_value(self, value: Optional[float]) -> str:
        """Format monetary value for contracts without raising runtime errors."""
        if value is None:
            return self.NOT_PROVIDE

        try:
            return locale.currency(value, grouping=True, symbol=False)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid asset value for contract currency formatting: {}", value
            )
            return self.NOT_PROVIDE

    def __build_lending_attachments_context(
        self, lending_attachments: List[LendingAttachments]
    ) -> List[dict]:
        """Convert lending attachments to base64 image payload expected by templates."""
        attachments_files: List[dict] = []
        for attachment in lending_attachments:
            if not attachment.path:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=[
                        {
                            "field": "attachments",
                            "error": "Anexo sem caminho de arquivo válido.",
                        }
                    ],
                )

            if not os.path.exists(attachment.path):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=[
                        {
                            "field": "attachments",
                            "error": (
                                "Arquivo de anexo não encontrado para geração do contrato."
                            ),
                        }
                    ],
                )

            try:
                attachments_files.append({"file": get_image_to_pdf(attachment.path)})
            except (OSError, ValueError, TypeError) as error:
                logger.warning(
                    "Unable to process lending attachment '{}': {}",
                    attachment.path,
                    error,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=[
                        {
                            "field": "attachments",
                            "error": "Não foi possível processar um dos anexos do comodato.",
                        }
                    ],
                ) from error

        return attachments_files

    def __validate_witnesses(
        self, witnesses: List[int], db_session: Session
    ) -> List[WitnessModel]:
        """Validate witnesses"""
        errors = []
        witnesses_validated = []
        ids_not_found = []
        for witness in witnesses:
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
                witnesses_validated.append(new_witness)

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

        return witnesses_validated

    def __validate_lending_contract_context(
        self,
        employee: EmployeeModel,
        workload,
        cost_center,
        witnesses: Optional[List[WitnessModel]] = None,
    ) -> List[dict]:
        """Validate required contract context to avoid runtime errors."""
        errors: List[dict] = []

        if not cost_center:
            errors.append(
                {"field": "costCenterId", "error": "Centro de custo não encontrado"}
            )

        if not workload:
            errors.append({"field": "workloadId", "error": "Lotação não encontrada"})

        if not employee.nationality:
            errors.append(
                {"field": "nationality", "error": "Nacionalidade não informada"}
            )

        if not employee.marital_status:
            errors.append(
                {"field": "maritalStatus", "error": "Estado civil não informado"}
            )

        if employee.legal_person:
            if not employee.role and not employee.job_position:
                errors.append({"field": "role", "error": "Cargo não informado"})
            if not employee.employer_contract_date:
                errors.append(
                    {
                        "field": "employerContractDate",
                        "error": "Data do contrato PJ não informada",
                    }
                )
            if not employee.employer_number:
                errors.append(
                    {"field": "employerNumber", "error": "CNPJ não informado"}
                )
            if not employee.employer_name:
                errors.append(
                    {"field": "employerName", "error": "Razão social não informada"}
                )
        else:
            if not employee.role:
                errors.append({"field": "role", "error": "Cargo não informado"})

        if witnesses is not None and len(witnesses) < 2:
            errors.append(
                {
                    "field": "witnessesId",
                    "error": "Necessário informar 2 testemunhas",
                }
            )

        return errors

    def serialize_document(self, doc: DocumentModel) -> DocumentSerializerSchema:
        """Serialize document"""
        return DocumentSerializerSchema(
            id=doc.id,
            type=doc.doc_type.name,
            path=doc.path,
            file_name=doc.file_name,
        )

    def __cleanup_generated_contract_file(self, file_path: Optional[str]) -> None:
        """Remove contrato gerado no filesystem quando ocorre falha no fluxo."""
        if not file_path:
            return

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.warning(
                    "Arquivo de contrato removido após falha no fluxo: {}",
                    file_path,
                )
        except OSError as cleanup_error:
            logger.error(
                "Falha ao remover arquivo de contrato após erro. path={}, erro={}",
                file_path,
                str(cleanup_error),
            )

    def create_contract(
        self,
        new_lending_doc: NewLendingDocSchema,
        type_doc: str,
        db_session: Session,
        authenticated_user: UserModel,
        auto_commit: bool = True,
    ) -> DocumentSerializerSchema:
        """Create new contract, not signed"""
        contract_path: Optional[str] = None
        try:
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

            if not current_lending:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "field": "lendingId",
                        "error": "Contrato de Comodato não encontrado",
                    },
                )

            dependency_errors: List[dict] = []
            if not doc_type:
                dependency_errors.append(
                    {
                        "field": "general",
                        "error": f"Tipo de documento '{type_doc}' não encontrado.",
                    }
                )
            if not lending_pending:
                dependency_errors.append(
                    {
                        "field": "general",
                        "error": "Status de comodato 'Arquivo pendente' não encontrado.",
                    }
                )
            if not current_lending.asset:
                dependency_errors.append(
                    {"field": "assetId", "error": "Ativo não encontrado"}
                )

            if dependency_errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=dependency_errors,
                )

            asset = current_lending.asset

            new_code = current_lending.number or self.__generate_code(
                db_session.query(DocumentModel)
                .order_by(DocumentModel.id.desc())
                .first(),
                asset,
            )

            workload = current_lending.workload

            employee = current_lending.employee

            validation_errors = self.__validate_lending_contract_context(
                employee=employee,
                workload=workload,
                cost_center=current_lending.cost_center,
                witnesses=current_lending.witnesses,
            )
            if validation_errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=validation_errors
                )

            witness1 = current_lending.witnesses[0]

            witness2 = current_lending.witnesses[1]

            detail = self.__get_contract_detail(
                asset, current_lending.cost_center.code, current_lending.ms_office
            )

            lending_attachments = (
                db_session.query(LendingAttachments)
                .join(LendingModel)
                .filter(LendingModel.id == current_lending.id)
                .all()
            )
            lending_verification_answers = (
                db_session.query(VerificationAnswerModel)
                .join(LendingModel)
                .filter(LendingModel.id == current_lending.id)
                .all()
            )
            verification_answers = self.__get_verification_answers(
                lending_verification_answers
            )
            attachments_files = self.__build_lending_attachments_context(
                lending_attachments
            )
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
                        role=(
                            employee.role.name
                            if employee.role
                            else employee.job_position
                        ),
                        marital_status=employee.marital_status.description,
                        cc=current_lending.cost_center.code,
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
                        company_address=(
                            employee.employer_address
                            if employee.employer_address
                            else employee.address
                        ),
                        object=(
                            employee.employer_contract_object
                            if employee.employer_contract_object
                            else ""
                        ),
                        company=employee.employer_name,
                        project=current_lending.project or self.NOT_PROVIDE,
                        location=current_lending.location,
                        contract_date=employee.employer_contract_date.strftime(
                            DEFAULT_DATE_FORMAT
                        ),
                        bu=current_lending.bu,
                        verifications=verification_answers,
                        attachments_files=attachments_files,
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
                        role=employee.role.name if employee.role else self.NOT_PROVIDE,
                        marital_status=employee.marital_status.description,
                        cc=current_lending.cost_center.code,
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
                        project=current_lending.project or self.NOT_PROVIDE,
                        location=current_lending.location,
                        bu=current_lending.bu,
                        verifications=verification_answers,
                        attachments_files=attachments_files,
                    )
                )

            filename = f"{new_code}.pdf"

            new_doc = DocumentModel(
                path=contract_path,
                file_name=filename,
                sign_doc_id=None,
                sign_envelope_id=None,
            )
            new_doc.doc_type = doc_type

            db_session.add(new_doc)
            db_session.flush()

            service_log.set_log(
                "lending",
                "document",
                f"Criação de {type_doc}",
                new_doc.id,
                authenticated_user,
                db_session,
                auto_commit=False,
            )
            logger.info("New Document. {}", str(new_doc))

            db_session.add(asset)
            db_session.flush()

            current_lending.document = new_doc
            current_lending.number = new_code
            current_lending.status = lending_pending

            db_session.add(current_lending)
            db_session.flush()

            service_log.set_log(
                "lending",
                "lending",
                "Vinculação do Contrato ao Comodato",
                current_lending.id,
                authenticated_user,
                db_session,
                auto_commit=False,
            )
            logger.info("New Document add to Lending. {}", str(current_lending))

            if auto_commit:
                db_session.commit()
            else:
                db_session.flush()

            return self.serialize_document(new_doc)
        except HTTPException as error:
            self.__cleanup_generated_contract_file(contract_path)
            if auto_commit:
                db_session.rollback()
            logger.warning(
                "Contract creation failed with HTTP {}: {}",
                error.status_code,
                error.detail,
            )
            raise
        except Exception as error:
            self.__cleanup_generated_contract_file(contract_path)
            if auto_commit:
                db_session.rollback()
            logger.exception("Unexpected error creating contract: {}", error)
            raise

    def recreate_contract(
        self,
        recreate_lending_doc: RecrateLendingDocSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Recreate new contract, not signed"""
        try:
            doc = None
            if recreate_lending_doc.document_id:
                doc = self.__get_document_or_404(
                    recreate_lending_doc.document_id, db_session
                )

            current_lending = (
                db_session.query(LendingModel)
                .filter(LendingModel.id == recreate_lending_doc.lending_id)
                .first()
            )
            if not current_lending:
                db_session.close()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "field": "lendingId",
                        "error": "Contrato de Comodato não encontrado",
                    },
                )

            workload = current_lending.workload

            employee = current_lending.employee

            validation_errors = self.__validate_lending_contract_context(
                employee=employee,
                workload=workload,
                cost_center=current_lending.cost_center,
                witnesses=current_lending.witnesses,
            )
            if validation_errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=validation_errors
                )

            witness1 = current_lending.witnesses[0]

            witness2 = current_lending.witnesses[1]

            detail = self.__get_contract_detail(
                current_lending.asset,
                current_lending.cost_center.code,
                current_lending.ms_office,
            )

            code = current_lending.number or self.__generate_code(
                db_session.query(DocumentModel)
                .order_by(DocumentModel.id.desc())
                .first(),
                current_lending.asset,
            )

            lending_attachments = (
                db_session.query(LendingAttachments)
                .join(LendingModel)
                .filter(LendingModel.id == current_lending.id)
                .all()
            )
            lending_verification_answers = (
                db_session.query(VerificationAnswerModel)
                .join(LendingModel)
                .filter(LendingModel.id == current_lending.id)
                .all()
            )
            verification_answers = self.__get_verification_answers(
                lending_verification_answers
            )
            lending_attachments_str = self.__build_lending_attachments_context(
                lending_attachments
            )

            if employee.legal_person:
                contract_path = create_lending_contract_pj(
                    NewLendingPjContextSchema(
                        number=code,
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
                        role=(
                            employee.role.name
                            if employee.role
                            else employee.job_position
                        ),
                        marital_status=employee.marital_status.description,
                        cc=current_lending.cost_center.code,
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
                        company_address=(
                            employee.employer_address
                            if employee.employer_address
                            else employee.address
                        ),
                        object=employee.employer_contract_object,
                        company=employee.employer_name,
                        project=current_lending.project,
                        location=current_lending.location,
                        contract_date=employee.employer_contract_date.strftime(
                            DEFAULT_DATE_FORMAT
                        ),
                        bu=current_lending.bu,
                        verifications=verification_answers,
                        attachments_files=lending_attachments_str,
                    )
                )
            else:
                contract_path = create_lending_contract(
                    NewLendingContextSchema(
                        number=code,
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
                        role=(
                            employee.role.name if employee.role else self.NOT_PROVIDE
                        ),
                        marital_status=employee.marital_status.description,
                        cc=current_lending.cost_center.code,
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
                        project=current_lending.project,
                        location=current_lending.location,
                        bu=current_lending.bu,
                        verifications=verification_answers,
                        attachments_files=lending_attachments_str,
                    )
                )
            filename = f"{code}.pdf"

            if doc:
                doc_type = doc.doc_type
                doc.deleted = True
                db_session.add(doc)
                db_session.commit()
            else:
                type_str = (
                    "Contrato de Comodato"
                    if current_lending.document_revoke_id is None
                    else "Distrato de Comodato"
                )
                doc_type = (
                    db_session.query(DocumentTypeModel)
                    .filter(DocumentTypeModel.name == type_str)
                    .first()
                )

            new_doc = DocumentModel(
                path=contract_path,
                file_name=filename,
                sign_doc_id=None,
                sign_envelope_id=doc.sign_envelope_id if doc else None,
                doc_type=doc_type,
            )

            db_session.add(new_doc)
            db_session.commit()
            db_session.flush()

            service_log.set_log(
                "lending",
                "document",
                f"Reriação de {new_doc.doc_type}",
                new_doc.id,
                authenticated_user,
                db_session,
            )
            logger.info("New Document. {}", str(new_doc))

            current_lending.document = new_doc
            current_lending.signer_email = recreate_lending_doc.employee_signer
            current_lending.principal_email_signer = (
                recreate_lending_doc.principal_signer
            )

            db_session.add(current_lending)
            db_session.commit()
            db_session.flush()

            service_log.set_log(
                "lending",
                "lending",
                "Nova vinculação de Contrato ao Comodato",
                current_lending.id,
                authenticated_user,
                db_session,
            )
            logger.info("Recreate Document add to Lending. {}", str(current_lending))

            return self.serialize_document(new_doc)
        except ValidationError as error:
            db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error.errors(),
            ) from error

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

        code = current_lending.number or self.__generate_code(
            db_session.query(DocumentModel).order_by(DocumentModel.id.desc()).first(),
            current_lending.asset,
        )

        workload = current_lending.workload

        employee = current_lending.employee

        validation_errors = self.__validate_lending_contract_context(
            employee=employee,
            workload=workload,
            cost_center=current_lending.cost_center,
            witnesses=current_lending.witnesses,
        )

        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=validation_errors
            )

        revoke_witnesses = self.__validate_witnesses(
            revoke_lending_doc.witnesses_id, db_session
        )

        validation_errors = self.__validate_lending_contract_context(
            employee=employee,
            workload=workload,
            cost_center=current_lending.cost_center,
            witnesses=revoke_witnesses,
        )
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=validation_errors
            )

        witness1 = revoke_witnesses[0]

        witness2 = revoke_witnesses[1]

        detail = self.__get_contract_detail(
            asset, current_lending.cost_center.code, current_lending.ms_office
        )

        if employee.legal_person:
            contract_path = create_revoke_lending_contract_pj(
                NewLendingPjContextSchema(
                    number=code,
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
                    role=employee.role.name if employee.role else employee.job_position,
                    marital_status=employee.marital_status.description,
                    cc=current_lending.cost_center.code,
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
                    company_address=(
                        employee.employer_address
                        if employee.employer_address
                        else employee.address
                    ),
                    company=employee.employer_name,
                    object=employee.employer_contract_object,
                    project=current_lending.project,
                    contract_date=employee.employer_contract_date.strftime(
                        DEFAULT_DATE_FORMAT
                    ),
                    location=current_lending.location,
                    bu=current_lending.bu,
                )
            )
        else:
            contract_path = create_revoke_lending_contract(
                NewLendingContextSchema(
                    number=code,
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
                    role=employee.role.name if employee.role else self.NOT_PROVIDE,
                    marital_status=employee.marital_status.description,
                    cc=current_lending.cost_center.code,
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
                    company_address=employee.employer_address or self.NOT_PROVIDE,
                    company=employee.employer_name,
                    project=current_lending.project or self.NOT_PROVIDE,
                    location=current_lending.location,
                    bu=current_lending.bu,
                )
            )

        filename = f"{code} - distrato.pdf"
        new_doc = DocumentModel(
            path=contract_path,
            file_name=filename,
            sign_doc_id=None,
            sign_envelope_id=None,
        )

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
        logger.info("New Document. {}", str(new_doc))

        AssetService().update_asset_status(
            asset,
            db_session.query(AssetStatusModel).get(AssetStatusEnum.DISPONIVEL.value),
            db_session,
        )

        current_lending.document_revoke = new_doc
        current_lending.status = lending_pending
        current_lending.witnesses.append(witness1)
        current_lending.witnesses.append(witness2)
        current_lending.signer_email = revoke_lending_doc.employee_signer
        current_lending.principal_email_signer = revoke_lending_doc.principal_signer

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
        logger.info("New Document add to Lending. {}", str(current_lending))

        return self.serialize_document(new_doc)

    def recreate_revoke_contract(
        self,
        recreate_lending_doc: RecrateLendingDocSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Recreate new contract, not signed"""
        doc = self.__get_document_or_404(recreate_lending_doc.document_id, db_session)

        current_lending = (
            db_session.query(LendingModel)
            .filter(LendingModel.id == recreate_lending_doc.lending_id)
            .first()
        )

        workload = current_lending.workload

        employee = current_lending.employee

        validation_errors = self.__validate_lending_contract_context(
            employee=employee,
            workload=workload,
            cost_center=current_lending.cost_center,
            witnesses=current_lending.witnesses,
        )

        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=validation_errors
            )

        current_lending.witnesses.reverse()

        validation_errors = self.__validate_lending_contract_context(
            employee=employee,
            workload=workload,
            cost_center=current_lending.cost_center,
            witnesses=current_lending.witnesses,
        )
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=validation_errors
            )

        witness1 = current_lending.witnesses[0]

        witness2 = current_lending.witnesses[1]

        detail = self.__get_contract_detail(
            current_lending.asset,
            current_lending.cost_center.code,
            current_lending.ms_office,
        )

        code = current_lending.number or self.__generate_code(
            db_session.query(DocumentModel).order_by(DocumentModel.id.desc()).first(),
            current_lending.asset,
        )

        if employee.legal_person:
            contract_path = create_revoke_lending_contract_pj(
                NewLendingPjContextSchema(
                    number=code,
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
                    role=employee.role.name if employee.role else employee.job_position,
                    marital_status=employee.marital_status.description,
                    cc=current_lending.cost_center.code,
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
                    company_address=(
                        employee.employer_address
                        if employee.employer_address
                        else employee.address
                    ),
                    company=employee.employer_name,
                    object=employee.employer_contract_object,
                    project=current_lending.project,
                    contract_date=employee.employer_contract_date.strftime(
                        DEFAULT_DATE_FORMAT
                    ),
                    location=current_lending.location,
                    bu=current_lending.bu,
                )
            )
        else:
            contract_path = create_revoke_lending_contract(
                NewLendingContextSchema(
                    number=code,
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
                    role=employee.role.name if employee.role else self.NOT_PROVIDE,
                    marital_status=employee.marital_status.description,
                    cc=current_lending.cost_center.code,
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
                    bu=current_lending.bu,
                )
            )

        filename = f"{code} - distrato.pdf"
        new_doc = DocumentModel(
            path=contract_path,
            file_name=filename,
            sign_doc_id=None,
            sign_envelope_id=doc.sign_envelope_id,
        )

        new_doc.doc_type = doc.doc_type

        doc.deleted = True
        db_session.add(doc)
        db_session.commit()

        db_session.add(new_doc)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "document",
            f"Reriação de {doc.doc_type}",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document. {}", str(new_doc))

        current_lending.document = new_doc
        current_lending.signer_email = recreate_lending_doc.employee_signer
        current_lending.principal_email_signer = recreate_lending_doc.principal_signer

        db_session.add(current_lending)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "lending",
            "Nova vinculação de Distrato ao Comodato",
            current_lending.id,
            authenticated_user,
            db_session,
        )
        logger.info("Recreate Document add to Lending. {}", str(current_lending))

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

        if not code:
            code = self.__generate_code(
                db_session.query(DocumentModel)
                .order_by(DocumentModel.id.desc())
                .first(),
                lending.asset,
            )

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

        if lending.document:
            old_doc = lending.document
            old_doc.deleted = True
            db_session.add(old_doc)
            db_session.commit()
            db_session.flush()
            service_log.set_log(
                "lending",
                "document",
                f"Exclusão de Contrato {old_doc.doc_type}",
                old_doc.id,
                authenticated_user,
                db_session,
            )
            logger.info("Deleted Document. {}", str(old_doc))

        lending.signed_date = date.today()
        lending.document = new_doc
        lending.status = lending_signed
        if lending.number is None:
            lending.number = code
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
        logger.info("Upload Document signed. {}", str(new_doc))

        return self.serialize_document(new_doc)

    async def upload_contract_fix(
        self,
        contract: UploadFile,
        type_doc: str,
        lendingId: int,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Upload contract to fix"""

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

        if lending.document:
            old_doc = lending.document
            old_doc.deleted = True
            db_session.add(old_doc)
            db_session.commit()
            db_session.flush()
            service_log.set_log(
                "lending",
                "document",
                f"Exclusão de Contrato {old_doc.doc_type}",
                old_doc.id,
                authenticated_user,
                db_session,
            )
            logger.info("Deleted Document. {}", str(old_doc))

        lending.document = new_doc
        db_session.add(lending)
        db_session.commit()

        service_log.set_log(
            "lending",
            "document",
            f"Importação de Contrato {type_doc} corrigida",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("Upload Document signed. {}", str(new_doc))

        return self.serialize_document(new_doc)

    def create_term(
        self,
        new_term_doc: NewTermDocSchema,
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

        term_pending = (
            db_session.query(TermStatusModel)
            .filter(TermStatusModel.name == "Arquivo pendente")
            .first()
        )

        current_term = (
            db_session.query(TermModel)
            .filter(TermModel.id == new_term_doc.term_id)
            .first()
        )

        item = current_term.term_item

        new_code = self.__generate_code(
            db_session.query(DocumentModel).order_by(DocumentModel.id.desc()).first(),
            None,
            "term",
        )

        employee = current_term.employee

        detail = self.__get_term_detail(item, current_term.type.name)

        contract_path = create_term(
            NewTermContextSchema(
                number=new_code,
                full_name=employee.full_name,
                taxpayer_identification=employee.taxpayer_identification,
                national_identification=employee.national_identification,
                marital_status=employee.marital_status.description,
                address=employee.address,
                nationality=employee.nationality.description,
                role=employee.role.name,
                workload=current_term.workload.name,
                cc=current_term.cost_center.code,
                manager=current_term.manager,
                business_executive=current_term.business_executive,
                detail=detail,
                date=date.today().strftime(DEFAULT_DATE_FORMAT),
                project=current_term.project,
                location=current_term.location,
            )
        )

        filename = f"{new_code}.pdf"
        new_doc = DocumentModel(
            path=contract_path,
            file_name=filename,
            sign_doc_id=None,
            sign_envelope_id=None,
        )
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
        logger.info("New Document. {}", str(new_doc))

        current_term.document = new_doc
        current_term.number = new_code
        current_term.status = term_pending

        db_session.add(current_term)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "term",
            "Vinculação do Termo de Responsabilidade",
            current_term.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document add to Term. {}", str(current_term))

        return self.serialize_document(new_doc)

    def create_revoke_term(
        self,
        revoke_term_doc: NewRevokeTermDocSchema,
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

        term_pending = (
            db_session.query(TermStatusModel)
            .filter(TermStatusModel.name == "Arquivo de distrato pendente")
            .first()
        )

        current_term = (
            db_session.query(TermModel)
            .filter(TermModel.id == revoke_term_doc.term_id)
            .first()
        )

        item = current_term.term_item

        code = current_term.number

        employee = current_term.employee

        detail = self.__get_term_detail(item, current_term.type.name)

        contract_path = create_term(
            NewTermContextSchema(
                number=code,
                full_name=employee.full_name,
                taxpayer_identification=employee.taxpayer_identification,
                national_identification=employee.national_identification,
                address=employee.address,
                nationality=employee.nationality.description,
                marital_status=employee.marital_status.description,
                role=employee.role.name,
                workload=current_term.workload.name,
                cc=current_term.cost_center.code,
                business_executive=current_term.business_executive,
                manager=current_term.manager,
                detail=detail,
                date=date.today().strftime(DEFAULT_DATE_FORMAT),
                project=current_term.project,
                location=current_term.location,
            ),
            "distrato_termo.html",
        )

        filename = f"{code} - distrato.pdf"

        new_doc = DocumentModel(
            path=contract_path,
            file_name=filename,
            sign_doc_id=None,
            sign_envelope_id=None,
        )

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
        logger.info("New Document. {}", str(new_doc))

        current_term.document_revoke = new_doc
        current_term.status = term_pending
        current_term.signer_email = revoke_term_doc.employee_signer
        current_term.principal_email_signer = revoke_term_doc.principal_signer

        db_session.add(current_term)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "term",
            "Revogação de Termo de Responsabilidade",
            current_term.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Document add to Term. {}", str(current_term))

        return self.serialize_document(new_doc)

    async def upload_term(
        self,
        term_file: UploadFile,
        type_doc: str,
        termId: int,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Upload term"""

        doc_type = (
            db_session.query(DocumentTypeModel)
            .filter(DocumentTypeModel.name == type_doc)
            .first()
        )

        term_signed = (
            db_session.query(TermStatusModel)
            .filter(TermStatusModel.name == "Ativo")
            .first()
        )

        term = self.__get_term_or_404(termId, db_session)

        code = term.number

        file_name = f"{code}.pdf"

        UPLOAD_DIR = CONTRACT_UPLOAD_DIR

        if DEBUG:
            UPLOAD_DIR = os.path.join(BASE_DIR, "storage", "terms")

        file_path = await upload_file(
            file_name, "term", term_file.file.read(), UPLOAD_DIR
        )

        new_doc = DocumentModel(path=file_path, file_name=file_name)
        new_doc.doc_type = doc_type

        db_session.add(new_doc)
        db_session.commit()

        term.signed_date = date.today()
        term.document = new_doc
        term.status = term_signed
        db_session.add(term)
        db_session.commit()

        service_log.set_log(
            "lending",
            "document",
            f"Importação de Contrato {type_doc}",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("Upload Document signed. {}", str(new_doc))

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
            .filter(LendingStatusModel.name == "Distrato realizado")
            .first()
        )

        lending = self.__get_lending_or_404(lendingId, db_session)

        code = lending.number

        file_name = f"{code} - distrato.pdf"

        UPLOAD_DIR = CONTRACT_UPLOAD_DIR

        if DEBUG:
            UPLOAD_DIR = os.path.join(BASE_DIR, "storage", "contracts")

        file_path = await upload_file(
            file_name, "revoke", contract.file.read(), UPLOAD_DIR
        )

        new_doc = DocumentModel(path=file_path, file_name=file_name)
        new_doc.doc_type = doc_type

        db_session.add(new_doc)
        db_session.commit()

        AssetService().update_asset_status(
            lending.asset,
            db_session.query(AssetStatusModel).get(AssetStatusEnum.DISPONIVEL.value),
            db_session,
        )
        db_session.add(lending)
        db_session.commit()
        db_session.flush()

        if lending.document_revoke:
            old_doc = lending.document_revoke
            old_doc.deleted = True
            db_session.add(old_doc)
            db_session.commit()
            db_session.flush()
            service_log.set_log(
                "lending",
                "document",
                f"Exclusão de Distrato {old_doc.doc_type}",
                old_doc.id,
                authenticated_user,
                db_session,
            )
            logger.info("Deleted Document. {}", str(old_doc))

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
        logger.info("Upload Document renvoke. {}", str(new_doc))

        return self.serialize_document(new_doc)

    async def upload_revoke_term(
        self,
        term_file: UploadFile,
        type_doc: str,
        termId: int,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> DocumentSerializerSchema:
        """Upload term"""

        doc_type = (
            db_session.query(DocumentTypeModel)
            .filter(DocumentTypeModel.name == type_doc)
            .first()
        )

        term_signed = (
            db_session.query(TermStatusModel)
            .filter(TermStatusModel.name == "Distrato realizado")
            .first()
        )

        term = self.__get_term_or_404(termId, db_session)

        code = term.number

        file_name = f"{code}.pdf"

        UPLOAD_DIR = CONTRACT_UPLOAD_DIR

        if DEBUG:
            UPLOAD_DIR = os.path.join(BASE_DIR, "storage", "terms")

        file_path = await upload_file(
            file_name, "revoke", term_file.file.read(), UPLOAD_DIR
        )

        new_doc = DocumentModel(path=file_path, file_name=file_name)
        new_doc.doc_type = doc_type

        db_session.add(new_doc)
        db_session.commit()

        term.revoke_signed_date = date.today()
        term.document_revoke = new_doc
        term.status = term_signed
        db_session.add(term)
        db_session.commit()

        service_log.set_log(
            "lending",
            "document",
            f"Importação de Distrato {type_doc}",
            new_doc.id,
            authenticated_user,
            db_session,
        )
        logger.info("Upload Document renvoke. {}", str(new_doc))

        return self.serialize_document(new_doc)

    def get_documents(
        self,
        db_session: Session,
        document_filters: DocumentFilter,
        page: int = 1,
        size: int = 50,
    ) -> Page[DocumentSerializerSchema]:
        """Get documents list"""

        document_list = (
            document_filters.filter(
                db_session.query(DocumentModel).join(DocumentTypeModel)
            )
            .filter(DocumentModel.deleted.is_(False))
            .order_by(desc(DocumentModel.id))
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

    def __get_verification_answers(
        self, lending_verification_answers: List[VerificationAnswerModel]
    ) -> List[Dict]:
        verification_answers = []
        for answer in lending_verification_answers:
            verification = answer.verification
            options = []
            for option in verification.options:
                options.append(
                    {
                        "option": option.name,
                        "checked": option.name == answer.answer,
                        "id": option.id,
                    }
                )

            verification_answers.append(
                {
                    "question": verification.question,
                    "options": options,
                }
            )
        return verification_answers

    def get_verification_document(
        self,
        lendind_id: int,
        db_session: Session,
        authenticated_user: UserModel,
        new_code: str = "",
    ):
        """Get a verification document"""
        try:
            lending = self.__get_lending_or_404(lendind_id, db_session)
            lending_number = new_code or lending.number
            verification_file_name = f"{lending_number} - verificação.pdf"
            document = (
                db_session.query(DocumentModel)
                .filter(DocumentModel.file_name == verification_file_name)
                .first()
            )

            if document:
                return document

            lending_verification_answers = (
                db_session.query(VerificationAnswerModel)
                .join(LendingModel)
                .filter(LendingModel.id == lending.id)
                .all()
            )

            verifications_context = self.__get_verification_answers(
                lending_verification_answers
            )

            context = {
                "verifications": verifications_context,
                "number": lending_number,
            }
            verification_document_path = create_verification_document(
                VerificationContextSchema(**context)
            )
            new_doc = DocumentModel(
                path=verification_document_path,
                file_name=verification_file_name,
            )
            doc_type = (
                db_session.query(DocumentTypeModel)
                .filter(DocumentTypeModel.name == "Verificação")
                .first()
            )
            new_doc.doc_type = doc_type

            db_session.add(new_doc)
            db_session.commit()
            db_session.flush()

            service_log.set_log(
                "lending",
                "document",
                f"Criação de {doc_type}",
                new_doc.id,
                authenticated_user,
                db_session,
            )
            logger.info("New Document. {}", str(new_doc))
            return new_doc
        except ValidationError as error:
            db_session.rollback()
            logger.error("Error download verification document {}", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"field": "lendingId", "message": "Comodato sem número"},
            ) from error

    def sign_document(self, document_id: int, db_session: Session) -> None:
        """Sign document"""
        try:
            document = self.__get_document_or_404(document_id, db_session)
            lending = None
            term = None

            if document.doc_type_id == DocumentTypeEnum.LENDING:
                lending = (
                    db_session.query(LendingModel)
                    .filter(LendingModel.document_id == document.id)
                    .first()
                )
            elif document.doc_type_id == DocumentTypeEnum.REVOKE_LENDING:
                lending = (
                    db_session.query(LendingModel)
                    .filter(LendingModel.document_revoke_id == document.id)
                    .first()
                )
            elif document.doc_type_id == DocumentTypeEnum.TERM:
                term = (
                    db_session.query(TermModel)
                    .filter(TermModel.document_id == document.id)
                    .first()
                )
            elif document.doc_type_id == DocumentTypeEnum.REVOKE_TERM:
                term = (
                    db_session.query(TermModel)
                    .filter(TermModel.document_revoke_id == document.id)
                    .first()
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "field": "documentId",
                        "message": "Tipo de documento inválido para assinatura",
                    },
                )

            if document.doc_type_id in [
                DocumentTypeEnum.LENDING,
                DocumentTypeEnum.REVOKE_LENDING,
            ]:
                employee = lending.employee
                lending.witnesses.reverse()
                witness1 = lending.witnesses[0]
                witness2 = lending.witnesses[1]

                envelope_id, document_id = self.clicksign_service.send_document_to_sign(
                    document.file_name,
                    document.path,
                    lending.signer_email,
                    lending.principal_email_signer,
                    employee.full_name,
                    employee.taxpayer_identification,
                    employee.birthday.isoformat(),
                    [
                        {
                            "full_name": witness1.employee.full_name,
                            "taxpayer_id": witness1.employee.taxpayer_identification,
                            "birthday": witness1.employee.birthday.isoformat(),
                            "email": witness1.employee.email,
                        },
                        {
                            "full_name": witness2.employee.full_name,
                            "taxpayer_id": witness2.employee.taxpayer_identification,
                            "birthday": witness2.employee.birthday.isoformat(),
                            "email": witness2.employee.email,
                        },
                    ],
                )
            elif document.doc_type_id in [
                DocumentTypeEnum.TERM,
                DocumentTypeEnum.REVOKE_TERM,
            ]:
                employee = term.employee

                envelope_id, document_id = self.clicksign_service.send_document_to_sign(
                    document.file_name,
                    document.path,
                    term.signer_email,
                    term.principal_email_signer,
                    employee.full_name,
                    employee.taxpayer_identification,
                    employee.birthday.isoformat(),
                    [],
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "field": "documentId",
                        "message": "Tipo de documento inválido para assinatura",
                    },
                )

            document.sign_envelope_id = envelope_id
            document.sign_doc_id = document_id
            db_session.add(document)
            db_session.commit()
            logger.info("Document sent to sign. {}", str(document))
        except Exception as error:
            db_session.rollback()
            logger.error("Error sign document {}", error)
            logger.error("Document ID {}", document_id)
            logger.error("document {}", str(document))
            logger.error("document type {}", str(document.doc_type))
            logger.error("lending {}", str(lending))
            logger.error("employee {}", str(employee))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"field": "lendingId", "message": "Erro ao assinar contrato"},
            ) from error
