"""People service"""

import logging
import random
from typing import List, Union

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.config import DEFAULT_DATE_FORMAT
from src.datasync.models import (
    CostCenterTOTVSModel,
    EmployeeEducationalLevelTOTVSModel,
    EmployeeGenderTOTVSModel,
    EmployeeMaritalStatusTOTVSModel,
    EmployeeNationalityTOTVSModel,
    EmployeeRoleTOTVSModel,
)
from src.lending.models import LendingModel
from src.lending.schemas import CostCenterSerializerSchema
from src.lending.service import LendingService
from src.log.services import LogService
from src.people.filters import (
    CostCenterFilter,
    EmployeeEducationalLevelFilter,
    EmployeeFilter,
    EmployeeGenderFilter,
    EmployeeMaritalStatusFilter,
    EmployeeNationalityFilter,
    EmployeeRoleFilter,
)
from src.people.models import EmployeeModel
from src.people.schemas import (
    EmployeeEducationalLevelSerializerSchema,
    EmployeeGenderSerializerSchema,
    EmployeeMatrimonialStatusSerializerSchema,
    EmployeeNationalitySerializerSchema,
    EmployeeRoleSerializerSchema,
    EmployeeSerializerSchema,
    NewEmployeeSchema,
    UpdateEmployeeSchema,
)

logger = logging.getLogger(__name__)
service_log = LogService()


class EmployeeService:
    """Employee services"""

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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "employeeId", "error": "Colaborador não encontrado"},
            )
        return employee

    def __validate_nested(
        self, data: Union[NewEmployeeSchema, UpdateEmployeeSchema], db_session: Session
    ) -> tuple:
        """Validates role, nationality, marital status and gender values"""
        errors = []
        if data.role:
            role = (
                db_session.query(EmployeeRoleTOTVSModel)
                .filter(EmployeeRoleTOTVSModel.id == data.role)
                .first()
            )
            if not role:
                errors.append({"field": "roleId", "error": "Cargo não existe"})

        if data.nationality_id:
            nationality = (
                db_session.query(EmployeeNationalityTOTVSModel)
                .filter(EmployeeNationalityTOTVSModel.id == data.nationality_id)
                .first()
            )
            if not nationality:
                errors.append(
                    {"field": "nationalityId", "error": "Nacionalidade não existe"}
                )

        if data.marital_status_id:
            marital_status = (
                db_session.query(EmployeeMaritalStatusTOTVSModel)
                .filter(EmployeeMaritalStatusTOTVSModel.id == data.marital_status_id)
                .first()
            )
            if not marital_status:
                errors.append(
                    {"field": "maritalStatusId", "error": "Estado civil não existe"}
                )

        if data.gender_id:
            gender = (
                db_session.query(EmployeeGenderTOTVSModel)
                .filter(EmployeeGenderTOTVSModel.id == data.gender_id)
                .first()
            )
            if not gender:
                errors.append({"field": "genderId", "error": "Genero não existe"})

        if data.educational_level_id:
            educational_level = (
                db_session.query(EmployeeEducationalLevelTOTVSModel)
                .filter(
                    EmployeeEducationalLevelTOTVSModel.id == data.educational_level_id
                )
                .first()
            )
            if not educational_level:
                errors.append(
                    {
                        "field": "educationalLevelId",
                        "error": "Nível de Escolaridade não existe",
                    }
                )

        if len(errors) > 0:
            raise HTTPException(
                detail=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return (role, nationality, marital_status, gender, educational_level)

    def __generate_code(self, last_employee: EmployeeModel) -> str:
        """Generate new code for employee"""
        last_code = last_employee.id
        new_code = last_code + 1
        str_code = str(new_code)
        return "".join(
            random.choice(last_employee.full_name.replace(" ", "")) for _ in range(3)
        ) + str_code.zfill(16 - len(str_code))

    def serialize_employee(self, employee: EmployeeModel) -> EmployeeSerializerSchema:
        """Serialize employee"""
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
            code=employee.code,
            status=employee.status,
            full_name=employee.full_name,
            national_identification=employee.national_identification,
            taxpayer_identification=employee.taxpayer_identification,
            address=employee.address,
            cell_phone=employee.cell_phone,
            email=employee.email,
            birthday=employee.birthday.strftime(DEFAULT_DATE_FORMAT),
            manager=employee.manager,
            admission_date=(
                employee.admission_date.strftime(DEFAULT_DATE_FORMAT)
                if employee.admission_date
                else None
            ),
            registration=employee.registration,
            legal_person=employee.legal_person,
            employer_address=employee.employer_address,
            employer_name=employee.employer_name,
            employer_number=employee.employer_number,
            employer_contract_object=employee.employer_contract_object,
            employer_contract_date=(
                employee.employer_contract_date.strftime(DEFAULT_DATE_FORMAT)
                if employee.employer_contract_date
                else None
            ),
            employer_end_contract_date=(
                employee.employer_end_contract_date.strftime(DEFAULT_DATE_FORMAT)
                if employee.employer_end_contract_date
                else None
            ),
        )

    def create_employee(
        self,
        data: NewEmployeeSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> EmployeeSerializerSchema:
        """Creates new employee"""
        errors = []
        if data.code and (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.code == data.code)
            .first()
        ):
            errors.append({"field": "code", "error": "Colaborador já existe"})

        if data.taxpayer_identification and (
            db_session.query(EmployeeModel)
            .filter(
                EmployeeModel.taxpayer_identification == data.taxpayer_identification
            )
            .first()
        ):
            errors.append(
                {"field": "taxpayer_identification", "error": "Colaborador já existe"}
            )

        if len(errors) > 0:
            raise HTTPException(
                detail=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        (
            role,
            nationality,
            marital_status,
            gender,
            educational_level,
        ) = self.__validate_nested(data, db_session)

        new_registration = self.__generate_code(
            db_session.query(EmployeeModel).all()[-1]
        )

        new_emplyoee = EmployeeModel(
            registration=new_registration,
            code=data.code,
            full_name=data.full_name,
            taxpayer_identification=data.taxpayer_identification,
            national_identification=data.national_identification,
            address=data.address,
            cell_phone=data.cell_phone,
            email=data.email,
            birthday=data.birthday,
            manager=data.manager,
            legal_person=True,
            employer_number=data.employer_number,
            employer_address=data.employer_address,
            employer_contract_object=data.employer_contract_object,
            employer_contract_date=data.employer_contract_date,
            employer_name=data.employer_name,
        )

        new_emplyoee.role = role
        new_emplyoee.nationality = nationality
        new_emplyoee.marital_status = marital_status
        new_emplyoee.gender = gender
        new_emplyoee.educational_level = educational_level

        db_session.add(new_emplyoee)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "people",
            "employee",
            "Adição de Colaborador",
            new_emplyoee.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Employee. %s", str(new_emplyoee))
        return self.serialize_employee(new_emplyoee)

    def update_employee(
        self,
        employee_id: int,
        data: UpdateEmployeeSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> EmployeeSerializerSchema:
        """Uptades new employee"""
        employee = self.__get_employee_or_404(employee_id, db_session)
        if not employee.legal_person:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este colaborador não pode ser editado.",
            )

        (
            role,
            nationality,
            marital_status,
            gender,
            educational_level,
        ) = self.__validate_nested(data, db_session)
        if data.role:
            employee.role = role
        if data.nationality_id:
            employee.nationality = nationality
        if data.marital_status_id:
            employee.marital_status = marital_status
        if data.gender_id:
            employee.gender = gender
        if data.educational_level_id:
            employee.educational_level = educational_level
        if data.code:
            employee.code = data.code
        if data.full_name:
            employee.full_name = data.full_name
        if data.taxpayer_identification:
            employee.taxpayer_identification = data.taxpayer_identification
        if data.national_identification:
            employee.national_identification = data.national_identification
        if data.address:
            employee.address = data.address
        if data.cell_phone:
            employee.cell_phone = data.cell_phone
        if data.email:
            employee.email = data.email
        if data.birthday:
            employee.birthday = data.birthday
        if data.manager:
            employee.manager = data.manager
        if data.employer_number:
            employee.employer_number = data.employer_number
        if data.employer_address:
            employee.employer_address = data.employer_address
        if data.employer_name:
            employee.employer_name = data.employer_name
        if data.employer_contract_object:
            employee.employer_contract_object = data.employer_contract_object
        if data.employer_contract_date:
            employee.employer_contract_date = data.employer_contract_date
        if data.employer_end_contract_date:
            employee.employer_end_contract_date = data.employer_end_contract_date

        db_session.add(employee)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "people",
            "employee",
            "Edição de Colaborador",
            employee.id,
            authenticated_user,
            db_session,
        )
        logger.info("Updated Employee. %s", str(employee))
        return self.serialize_employee(employee)

    def get_employee(
        self, employee_id: int, db_session: Session
    ) -> EmployeeSerializerSchema:
        """Get an employee"""
        employee = self.__get_employee_or_404(employee_id, db_session)

        return self.serialize_employee(employee)

    def get_employee_lending_history(
        self, employee_id: int, db_session: Session
    ) -> List[dict]:
        """Get an employee lending history"""
        employee = self.__get_employee_or_404(employee_id, db_session)

        historic_model = (
            db_session.query(LendingModel)
            .filter(LendingModel.employee_id == employee.id)
            .order_by(desc(LendingModel.id))
            .all()
        )

        historic_serialize = [
            LendingService().serialize_lending(h).model_dump(by_alias=True)
            for h in historic_model
        ]

        return historic_serialize

    def get_employees(
        self,
        db_session: Session,
        employee_filters: EmployeeFilter,
        fields: str = "",
        page: int = 1,
        size: int = 50,
    ) -> Page[EmployeeSerializerSchema]:
        """Get employees list"""
        employee_list = employee_filters.filter(
            db_session.query(EmployeeModel)
            .outerjoin(EmployeeRoleTOTVSModel)
            .outerjoin(EmployeeEducationalLevelTOTVSModel)
            .join(EmployeeNationalityTOTVSModel)
            .join(EmployeeMaritalStatusTOTVSModel)
            .join(EmployeeGenderTOTVSModel)
        ).order_by(desc(EmployeeModel.id))

        if fields == "":
            params = Params(page=page, size=size)
            paginated = paginate(
                employee_list,
                params=params,
                transformer=lambda employee_list: [
                    self.serialize_employee(employee).model_dump(by_alias=True)
                    for employee in employee_list
                ],
            )
        else:
            list_fields = fields.split(",")
            params = Params(page=page, size=size)
            paginated = paginate(
                employee_list,
                params=params,
                transformer=lambda employee_list: [
                    self.serialize_employee(employee).model_dump(
                        include={*list_fields}, by_alias=True
                    )
                    for employee in employee_list
                ],
            )

        return paginated


class EmpleoyeeGeneralSerivce:
    """Employee general services"""

    def serialize_nationality(
        self, nationality: EmployeeNationalityTOTVSModel
    ) -> EmployeeNationalitySerializerSchema:
        """Serialize nationality"""
        return EmployeeNationalitySerializerSchema(**nationality.__dict__)

    def serialize_marital_status(
        self, marital_status: EmployeeMaritalStatusTOTVSModel
    ) -> EmployeeMatrimonialStatusSerializerSchema:
        """Serialize marital status"""
        return EmployeeMatrimonialStatusSerializerSchema(**marital_status.__dict__)

    def serialize_cost_center(
        self, cost_center: CostCenterTOTVSModel
    ) -> CostCenterSerializerSchema:
        """Serialize cost center"""
        return CostCenterSerializerSchema(**cost_center.__dict__)

    def serialize_gender(
        self, gender: EmployeeGenderTOTVSModel
    ) -> EmployeeGenderSerializerSchema:
        """Serialize gender"""
        return EmployeeGenderSerializerSchema(**gender.__dict__)

    def serialize_role(
        self, role: EmployeeRoleTOTVSModel
    ) -> EmployeeRoleSerializerSchema:
        """Serialize role"""
        return EmployeeRoleSerializerSchema(**role.__dict__)

    def serialize_educational_level(
        self, educational_level: EmployeeEducationalLevelTOTVSModel
    ) -> EmployeeEducationalLevelSerializerSchema:
        """Serialize educational_level"""
        return EmployeeEducationalLevelSerializerSchema(**educational_level.__dict__)

    def get_nationalities(
        self,
        db_session: Session,
        nationality_filters: EmployeeNationalityFilter,
        fields: str = "",
    ) -> List[EmployeeNationalitySerializerSchema]:
        """Get nationalities list"""

        nationalities_list = nationality_filters.filter(
            db_session.query(EmployeeNationalityTOTVSModel)
        ).order_by(desc(EmployeeNationalityTOTVSModel.id))

        if fields == "":
            return [
                self.serialize_nationality(nationality).model_dump(by_alias=True)
                for nationality in nationalities_list
            ]
        list_fields = fields.split(",")
        return [
            self.serialize_nationality(nationality).model_dump(
                include={*list_fields}, by_alias=True
            )
            for nationality in nationalities_list
        ]

    def get_marital_status(
        self,
        db_session: Session,
        marital_status_filter: EmployeeMaritalStatusFilter,
        fields: str = "",
    ) -> List[EmployeeMatrimonialStatusSerializerSchema]:
        """Get marital status list"""

        marital_status_list = marital_status_filter.filter(
            db_session.query(EmployeeMaritalStatusTOTVSModel)
        ).order_by(desc(EmployeeMaritalStatusTOTVSModel.id))

        if fields == "":
            return [
                self.serialize_marital_status(marital_status).model_dump(by_alias=True)
                for marital_status in marital_status_list
            ]
        list_fields = fields.split(",")
        return [
            self.serialize_marital_status(marital_status).model_dump(
                include={*list_fields}, by_alias=True
            )
            for marital_status in marital_status_list
        ]

    def get_center_cost(
        self,
        db_session: Session,
        center_cost_filter: CostCenterFilter,
        fields: str = "",
    ) -> List[CostCenterSerializerSchema]:
        """Get center cost list"""

        center_cost_list = center_cost_filter.filter(
            db_session.query(CostCenterTOTVSModel)
        ).order_by(desc(CostCenterTOTVSModel.id))

        if fields == "":
            return [
                self.serialize_cost_center(center_cost).model_dump(by_alias=True)
                for center_cost in center_cost_list
            ]
        list_fields = fields.split(",")
        return [
            self.serialize_cost_center(center_cost).model_dump(
                include={*list_fields}, by_alias=True
            )
            for center_cost in center_cost_list
        ]

    def get_genders(
        self,
        db_session: Session,
        genders_filters: EmployeeGenderFilter,
        fields: str = "",
    ) -> List[EmployeeGenderSerializerSchema]:
        """Get genders list"""

        genders_list = genders_filters.filter(
            db_session.query(EmployeeGenderTOTVSModel)
        ).order_by(desc(EmployeeGenderTOTVSModel.id))

        if fields == "":
            return [
                self.serialize_gender(gender).model_dump(by_alias=True)
                for gender in genders_list
            ]

        list_fields = fields.split(",")
        return [
            self.serialize_gender(gender).model_dump(
                include={*list_fields}, by_alias=True
            )
            for gender in genders_list
        ]

    def get_roles(
        self,
        db_session: Session,
        roles_filter: EmployeeRoleFilter,
        fields: str = "",
    ) -> List[EmployeeRoleSerializerSchema]:
        """Get roles list"""

        roles_list = roles_filter.filter(
            db_session.query(EmployeeRoleTOTVSModel)
        ).order_by(desc(EmployeeRoleTOTVSModel.id))

        if fields == "":
            return [
                self.serialize_role(role).model_dump(by_alias=True)
                for role in roles_list
            ]

        list_fields = fields.split(",")
        return [
            self.serialize_role(role).model_dump(include={*list_fields}, by_alias=True)
            for role in roles_list
        ]

    def get_educational_levels(
        self,
        db_session: Session,
        educational_level_filter: EmployeeEducationalLevelFilter,
        fields: str = "",
    ) -> List[EmployeeEducationalLevelSerializerSchema]:
        """Get educational levels list"""

        educational_levels_list = educational_level_filter.filter(
            db_session.query(EmployeeEducationalLevelTOTVSModel)
        ).order_by(desc(EmployeeEducationalLevelTOTVSModel.id))

        if fields == "":
            return [
                self.serialize_educational_level(role).model_dump(by_alias=True)
                for role in educational_levels_list
            ]

        list_fields = fields.split(",")
        return [
            self.serialize_educational_level(role).model_dump(
                include={*list_fields}, by_alias=True
            )
            for role in educational_levels_list
        ]
