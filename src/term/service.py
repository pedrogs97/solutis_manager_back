"""Lenging service"""

import locale
import logging

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.config import DEFAULT_DATE_FORMAT
from src.datasync.models import CostCenterTOTVSModel
from src.lending.models import WorkloadModel
from src.lending.schemas import CostCenterSerializerSchema, WorkloadSerializerSchema
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
from src.term.filters import TermFilter
from src.term.models import TermItemModel, TermItemTypeModel, TermModel, TermStatusModel
from src.term.schemas import (
    NewTermSchema,
    TermItemSerializerSchema,
    TermSerializerSchema,
    UpdateTermSchema,
)

logger = logging.getLogger(__name__)
service_log = LogService()
locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")


class TermService:
    """Term service"""

    def __get_term_or_404(self, term_id: int, db_session: Session) -> TermModel:
        """Get term or 404"""
        term = db_session.query(TermModel).filter(TermModel.id == term_id).first()
        if not term:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "termId",
                    "error": "Termo de Responsabilidade não encontrado",
                },
            )

        return term

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

    def serialize_term(self, term: TermModel) -> TermSerializerSchema:
        """Serialize term"""
        return TermSerializerSchema(
            id=term.id,
            employee=self.serialize_employee(term.employee),
            document=term.document.id if term.document else None,
            document_revoke=(term.document_revoke.id if term.document_revoke else None),
            workload=(
                WorkloadSerializerSchema(**term.workload.__dict__)
                if term.workload
                else None
            ),
            cost_center=CostCenterSerializerSchema(**term.cost_center.__dict__),
            manager=term.manager,
            observations=term.observations,
            signed_date=(
                term.signed_date.strftime(DEFAULT_DATE_FORMAT)
                if term.signed_date
                else None
            ),
            revoke_signed_date=(
                term.revoke_signed_date.strftime(DEFAULT_DATE_FORMAT)
                if term.revoke_signed_date
                else None
            ),
            glpi_number=term.glpi_number,
            type=term.type.name,
            status=term.status.name if term.status else "",
            business_executive=term.business_executive,
            project=term.project,
            location=term.location,
            number=term.number,
            item=TermItemSerializerSchema(**term.term_item.__dict__),
        )

    def serialize_workload(self, workload: WorkloadModel) -> WorkloadSerializerSchema:
        """Serialize workload"""
        return WorkloadSerializerSchema(**workload.__dict__)

    def __validate_nested(self, data: NewTermSchema, db_session: Session) -> tuple:
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
                        "error": f"Tipo de Colaborador não existe. {data.employee_id}",
                    }
                )

        if data.type_id:
            termType = (
                db_session.query(TermItemTypeModel)
                .filter(TermItemTypeModel.id == data.type_id)
                .first()
            )
            if not termType:
                errors.append(
                    {
                        "field": "typeId",
                        "error": f"Tipo de termo não existe. {data.type_id}",
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
                    {
                        "field": "workloadId",
                        "error": f"Lotação não existe. {data.workload_id}",
                    }
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
                        "error": f"Centro de Custo não existe. {data.cost_center_id}",
                    }
                )

        if errors:
            raise HTTPException(
                detail=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return (
            employee,
            workload,
            cost_center,
            termType,
        )

    def create_term(
        self,
        new_term: NewTermSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ):
        """Creates new term"""

        (
            employee,
            workload,
            cost_center,
            termType,
        ) = self.__validate_nested(new_term, db_session)

        new_term_db = TermModel(
            manager=new_term.manager,
            observations=new_term.observations,
            glpi_number=new_term.glpi_number,
            business_executive=new_term.business_executive,
            project=new_term.project,
            location=new_term.location,
        )

        new_term_db.type = termType
        new_term_db.employee = employee
        new_term_db.workload = workload
        new_term_db.cost_center = cost_center

        db_session.add(new_term_db)
        db_session.commit()
        db_session.flush()

        if termType.name == "Kit Ferramenta":
            new_term_item = TermItemModel(description=new_term.description)
            new_term_item.term = new_term_db
        else:
            new_term_item = TermItemModel(
                size=new_term.size,
                quantity=new_term.quantity,
                value=new_term.value,
            )
            new_term_item.term = new_term_db

        db_session.add(new_term_item)
        db_session.add(new_term_db)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "term",
            "term",
            "Criação de Termo de Responsabilidade",
            new_term_db.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Term. %s", str(new_term_db))

        return self.serialize_term(new_term_db)

    def get_term(self, term_id: int, db_session: Session) -> TermSerializerSchema:
        """Get a term"""
        term = self.__get_term_or_404(term_id, db_session)
        return self.serialize_term(term)

    def update_term(
        self,
        term_id: int,
        data: UpdateTermSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> TermSerializerSchema:
        """Update a term"""
        term = self.__get_term_or_404(term_id, db_session)

        term.observations = data.observations
        db_session.add(term)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "term",
            "term",
            f"Atualização de Termo de Responsabilidade",
            term.id,
            authenticated_user,
            db_session,
        )
        logger.info("Update Term. %s", str(term))

        return self.serialize_term(term)

    def get_terms(
        self,
        db_session: Session,
        term_filters: TermFilter,
        page: int = 1,
        size: int = 50,
    ) -> Page[TermSerializerSchema]:
        """Get terms list"""

        term_list = term_filters.filter(
            db_session.query(TermModel)
            .join(TermItemTypeModel)
            .outerjoin(EmployeeModel)
            .outerjoin(WorkloadModel)
            .outerjoin(CostCenterTOTVSModel)
            .outerjoin(TermStatusModel)
        ).order_by(desc(TermModel.id))

        params = Params(page=page, size=size)
        paginated = paginate(
            term_list,
            params=params,
            transformer=lambda term_list: [
                self.serialize_term(term).model_dump(by_alias=True)
                for term in term_list
            ],
        )
        return paginated
