"""People service"""
import logging
from typing import List

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.lending.models import LendingModel
from src.lending.schemas import CostCenterSerializerSchema, LendingSerializerSchema
from src.lending.service import LendingService
from src.log.services import LogService
from src.people.models import (
    CostCenterModel,
    EmployeeGenderModel,
    EmployeeMaritalStatusModel,
    EmployeeModel,
    EmployeeNationalityModel,
    EmployeeRoleModel,
)
from src.people.schemas import (
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
                detail={"field": "employee", "error": "Colaborador não encontrado"},
            )
        return employee

    def __validate_nested(self, data: NewEmployeeSchema, db_session: Session) -> tuple:
        """Validates role, nationality, marital status and gender values"""
        errors = {}
        if data.role:
            role = (
                db_session.query(EmployeeRoleModel)
                .filter(EmployeeRoleModel.name == data.role)
                .first()
            )
            if not role:
                errors.update({"field": "role", "error": "Cargo não existe"})

        if data.nationality:
            nationality = (
                db_session.query(EmployeeNationalityModel)
                .filter(EmployeeNationalityModel.description == data.nationality)
                .first()
            )
            if not nationality:
                errors.update(
                    {"field": "nationality", "error": "Nacionalidade não existe"}
                )

        if data.marital_status:
            marital_status = (
                db_session.query(EmployeeMaritalStatusModel)
                .filter(EmployeeMaritalStatusModel.description == data.marital_status)
                .first()
            )
            if not marital_status:
                errors.update(
                    {"field": "maritalStatus", "error": "Estado civil não existe"}
                )

        if data.gender:
            gender = (
                db_session.query(EmployeeGenderModel)
                .filter(EmployeeGenderModel.description == data.gender)
                .first()
            )
            if not gender:
                errors.update({"field": "gender", "error": "Genero não existe"})

        if len(errors.keys()) > 0:
            raise HTTPException(
                detail=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return (role, nationality, marital_status, gender)

    def serialize_employee(self, employee: EmployeeModel) -> EmployeeSerializerSchema:
        """Serialize employee"""
        return EmployeeSerializerSchema(
            id=employee.id,
            role=EmployeeRoleSerializerSchema(**employee.role.__dict__)
            if employee.role
            else None,
            nationality=EmployeeNationalitySerializerSchema(
                **employee.nationality.__dict__
            ),
            marital_status=EmployeeMatrimonialStatusSerializerSchema(
                **employee.marital_status.__dict__
            ),
            gender=EmployeeGenderSerializerSchema(**employee.gender.__dict__),
            status=employee.status,
            manager=employee.manager,
            address=employee.address,
            birthday=employee.birthday.isoformat(),
            cell_phone=employee.cell_phone,
            code=employee.code,
            email=employee.email,
            full_name=employee.full_name,
            legal_person=employee.legal_person,
            national_identification=employee.national_identification,
            taxpayer_identification=employee.taxpayer_identification,
        )

    def create_employee(
        self,
        data: NewEmployeeSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> EmployeeSerializerSchema:
        """Creates new employee"""
        errors = {}
        if data.code and (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.code == data.code)
            .first()
        ):
            errors.update({"field": "code", "error": "Colaborador já existe"})

        if data.taxpayer_identification and (
            db_session.query(EmployeeModel)
            .filter(
                EmployeeModel.taxpayer_identification == data.taxpayer_identification
            )
            .first()
        ):
            errors.update(
                {"field": "taxpayer_identification", "error": "Colaborador já existe"}
            )

        if len(errors.keys()) > 0:
            raise HTTPException(
                detail=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        (role, nationality, marital_status, gender) = self.__validate_nested(
            data, db_session
        )
        new_emplyoee = EmployeeModel(
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
        )

        new_emplyoee.role = role
        new_emplyoee.nationality = nationality
        new_emplyoee.marital_status = marital_status
        new_emplyoee.gender = gender

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

        (role, nationality, marital_status, gender) = self.__validate_nested(
            data, db_session
        )
        if data.role:
            employee.role = role
        if data.nationality:
            employee.nationality = nationality
        if data.marital_status:
            employee.marital_status = marital_status
        if data.gender:
            employee.gender = gender
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
    ) -> List[LendingSerializerSchema]:
        """Get an employee lending history"""
        employee = self.__get_employee_or_404(employee_id, db_session)

        historic_model = (
            db_session.query(LendingModel)
            .filter(LendingModel.employee_id == employee.id)
            .all()
        )

        historic_serialize = [
            LendingService().serialize_lending(h) for h in historic_model
        ]

        return historic_serialize

    def get_employees(
        self,
        db_session: Session,
        search: str = "",
        filter_list: str = "",
        fields: str = "",
        page: int = 1,
        size: int = 50,
    ) -> Page[EmployeeSerializerSchema]:
        """Get employees list"""
        employee_list = db_session.query(EmployeeModel).filter(
            or_(
                EmployeeModel.full_name.ilike(f"%{search}%"),
                EmployeeModel.email.ilike(f"%{search}"),
                EmployeeModel.national_identification.ilike(f"%{search}"),
                EmployeeModel.taxpayer_identification.ilike(f"%{search}"),
                EmployeeModel.cell_phone.ilike(f"%{search}"),
                EmployeeModel.manager.ilike(f"%{search}"),
                EmployeeModel.code.ilike(f"%{search}"),
            )
        )

        if filter_list != "":
            employee_list = employee_list.join(
                EmployeeModel.role,
            ).filter(
                or_(
                    EmployeeRoleModel.name.in_(filter_list),
                )
            )

            employee_list = employee_list.join(
                EmployeeModel.nationality,
            ).filter(
                or_(
                    EmployeeNationalityModel.description.in_(filter_list),
                )
            )

            employee_list = employee_list.join(
                EmployeeModel.marital_status,
            ).filter(
                or_(
                    EmployeeMaritalStatusModel.description.in_(filter_list),
                )
            )

            employee_list = employee_list.join(
                EmployeeModel.gender,
            ).filter(
                or_(
                    EmployeeGenderModel.description.in_(filter_list),
                )
            )
        if fields == "":
            params = Params(page=page, size=size)
            paginated = paginate(
                employee_list,
                params=params,
                transformer=lambda employee_list: [
                    self.serialize_employee(employee) for employee in employee_list
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
        self, nationality: EmployeeNationalityModel
    ) -> EmployeeNationalitySerializerSchema:
        """Serialize nationality"""
        return EmployeeNationalitySerializerSchema(**nationality.__dict__)

    def serialize_marital_status(
        self, marital_status: EmployeeMaritalStatusModel
    ) -> EmployeeMatrimonialStatusSerializerSchema:
        """Serialize marital status"""
        return EmployeeMatrimonialStatusSerializerSchema(**marital_status.__dict__)

    def serialize_cost_center(
        self, cost_center: CostCenterModel
    ) -> CostCenterSerializerSchema:
        """Serialize cost center"""
        return CostCenterSerializerSchema(**cost_center.__dict__)

    def serialize_gender(
        self, gender: EmployeeGenderModel
    ) -> EmployeeGenderSerializerSchema:
        """Serialize gender"""
        return EmployeeGenderSerializerSchema(**gender.__dict__)

    def serialize_role(self, role: EmployeeRoleModel) -> EmployeeRoleSerializerSchema:
        """Serialize role"""
        return EmployeeRoleSerializerSchema(**role.__dict__)

    def get_nationalities(
        self,
        db_session: Session,
        search: str = "",
        fields: str = "",
        page: int = 1,
        size: int = 50,
    ) -> Page[EmployeeNationalitySerializerSchema]:
        """Get nationalities list"""

        nationalities_list = db_session.query(EmployeeNationalityModel).filter(
            or_(
                EmployeeNationalityModel.description.ilike(f"%{search}%"),
                EmployeeNationalityModel.code.ilike(f"%{search}"),
            )
        )

        if fields == "":
            params = Params(page=page, size=size)
            paginated = paginate(
                nationalities_list,
                params=params,
                transformer=lambda nationalities_list: [
                    self.serialize_nationality(nationality)
                    for nationality in nationalities_list
                ],
            )
        else:
            list_fields = fields.split(",")
            params = Params(page=page, size=size)
            paginated = paginate(
                nationalities_list,
                params=params,
                transformer=lambda nationalities_list: [
                    self.serialize_nationality(nationality).model_dump(
                        include={*list_fields}
                    )
                    for nationality in nationalities_list
                ],
            )

        return paginated

    def get_marital_status(
        self,
        db_session: Session,
        search: str = "",
        fields: str = "",
        page: int = 1,
        size: int = 50,
    ) -> Page[EmployeeMatrimonialStatusSerializerSchema]:
        """Get marital status list"""

        marital_status_list = db_session.query(EmployeeMaritalStatusModel).filter(
            or_(
                EmployeeMaritalStatusModel.description.ilike(f"%{search}%"),
                EmployeeMaritalStatusModel.code.ilike(f"%{search}"),
            )
        )

        if fields == "":
            params = Params(page=page, size=size)
            paginated = paginate(
                marital_status_list,
                params=params,
                transformer=lambda marital_status_list: [
                    self.serialize_marital_status(marital_status)
                    for marital_status in marital_status_list
                ],
            )
        else:
            list_fields = fields.split(",")
            params = Params(page=page, size=size)
            paginated = paginate(
                marital_status_list,
                params=params,
                transformer=lambda marital_status_list: [
                    self.serialize_marital_status(marital_status).model_dump(
                        include={*list_fields}
                    )
                    for marital_status in marital_status_list
                ],
            )

        return paginated

    def get_center_cost(
        self,
        db_session: Session,
        search: str = "",
        fields: str = "",
        page: int = 1,
        size: int = 50,
    ) -> Page[CostCenterSerializerSchema]:
        """Get center cost list"""

        center_cost_list = db_session.query(CostCenterModel).filter(
            or_(
                CostCenterModel.classification.ilike(f"%{search}%"),
                CostCenterModel.code.ilike(f"%{search}"),
            )
        )

        if fields == "":
            params = Params(page=page, size=size)
            paginated = paginate(
                center_cost_list,
                params=params,
                transformer=lambda center_cost_list: [
                    self.serialize_cost_center(center_cost)
                    for center_cost in center_cost_list
                ],
            )
        else:
            list_fields = fields.split(",")
            params = Params(page=page, size=size)
            paginated = paginate(
                center_cost_list,
                params=params,
                transformer=lambda center_cost_list: [
                    self.serialize_cost_center(center_cost).model_dump(
                        include={*list_fields}
                    )
                    for center_cost in center_cost_list
                ],
            )

        return paginated

    def get_genders(
        self,
        db_session: Session,
        search: str = "",
        fields: str = "",
        page: int = 1,
        size: int = 50,
    ) -> Page[EmployeeGenderSerializerSchema]:
        """Get genders list"""

        genders_list = db_session.query(EmployeeGenderModel).filter(
            or_(
                EmployeeGenderModel.description.ilike(f"%{search}%"),
                EmployeeGenderModel.code.ilike(f"%{search}"),
            )
        )

        if fields == "":
            params = Params(page=page, size=size)
            paginated = paginate(
                genders_list,
                params=params,
                transformer=lambda genders_list: [
                    self.serialize_gender(gender) for gender in genders_list
                ],
            )
        else:
            list_fields = fields.split(",")
            params = Params(page=page, size=size)
            paginated = paginate(
                genders_list,
                params=params,
                transformer=lambda genders_list: [
                    self.serialize_gender(gender).model_dump(include={*list_fields})
                    for gender in genders_list
                ],
            )

        return paginated

    def get_roles(
        self,
        db_session: Session,
        search: str = "",
        fields: str = "",
        page: int = 1,
        size: int = 50,
    ) -> Page[EmployeeRoleSerializerSchema]:
        """Get roles list"""

        roles_list = db_session.query(EmployeeRoleModel).filter(
            or_(
                EmployeeRoleModel.name.ilike(f"%{search}%"),
                EmployeeRoleModel.code.ilike(f"%{search}"),
            )
        )

        if fields == "":
            params = Params(page=page, size=size)
            paginated = paginate(
                roles_list,
                params=params,
                transformer=lambda roles_list: [
                    self.serialize_role(role) for role in roles_list
                ],
            )
        else:
            list_fields = fields.split(",")
            params = Params(page=page, size=size)
            paginated = paginate(
                roles_list,
                params=params,
                transformer=lambda roles_list: [
                    self.serialize_role(role).model_dump(include={*list_fields})
                    for role in roles_list
                ],
            )

        return paginated
