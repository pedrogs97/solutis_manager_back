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
from src.lending.schemas import LendingSerializerSchema
from src.lending.service import LendingService
from src.log.services import LogService
from src.people.models import (
    EmployeeGenderModel,
    EmployeeMaritalStatusModel,
    EmployeeModel,
    EmployeeNationalityModel,
    EmployeeRoleModel,
)
from src.people.schemas import (
    EmployeeGenderSerializerSchema,
    EmployeeGenderTotvsSchema,
    EmployeeMatrimonialStatusSerializerSchema,
    EmployeeMatrimonialStatusTotvsSchema,
    EmployeeNationalitySerializerSchema,
    EmployeeNationalityTotvsSchema,
    EmployeeRoleSerializerSchema,
    EmployeeRoleTotvsSchema,
    EmployeeSerializerSchema,
    EmployeeTotvsSchema,
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
                detail={"employee": "Colaborador não encontrado"},
            )
        return employee

    def __validate_nested(self, data: NewEmployeeSchema, db_session: Session) -> tuple:
        """Validates role, nationality, marital status and gender values"""
        if data.role:
            role = (
                db_session.query(EmployeeRoleModel)
                .filter(EmployeeRoleModel.name == data.role)
                .first()
            )
            if not role:
                raise HTTPException(
                    detail={"role": "Perfil não existe"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.role:
            nationality = (
                db_session.query(EmployeeNationalityModel)
                .filter(EmployeeNationalityModel.description == data.nationality)
                .first()
            )
            if not nationality:
                raise HTTPException(
                    detail={"nationality": "Nacionalidade não existe"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.marital_status:
            marital_status = (
                db_session.query(EmployeeMaritalStatusModel)
                .filter(EmployeeMaritalStatusModel.description == data.marital_status)
                .first()
            )
            if not marital_status:
                raise HTTPException(
                    detail={"maritalStatus": "Estado civil não existe"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.gender:
            gender = (
                db_session.query(EmployeeGenderModel)
                .filter(EmployeeGenderModel.description == data.gender)
                .first()
            )
            if not gender:
                raise HTTPException(
                    detail={"gender": "Genero não existe"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        return (role, nationality, marital_status, gender)

    def serialize_employee(self, employee: EmployeeModel) -> EmployeeSerializerSchema:
        """Serialize employee"""
        return EmployeeSerializerSchema(
            id=employee.id,
            role=EmployeeRoleSerializerSchema(**employee.role)
            if employee.role
            else None,
            nationality=EmployeeNationalitySerializerSchema(
                **employee.nationality.__dict__
            ),
            marital_status=EmployeeMatrimonialStatusSerializerSchema(
                **employee.marital_status.__dict__
            ),
            gender=EmployeeGenderSerializerSchema(**employee.gender.__dict__),
            manager=employee.manager,
            address=employee.address,
            birthday=employee.birthday,
            cell_phone=employee.cell_phone,
            code=employee.code,
            email=employee.email,
            full_name=employee.full_name,
            legal_person=employee.legal_person,
            national_identification=employee.national_identification,
            taxpayer_identification=employee.taxpayer_identification,
        )

    def update_employee_totvs(
        self, totvs_employees: List[EmployeeTotvsSchema], db_session: Session
    ):
        """Updates employees from totvs"""
        try:
            updates: List[EmployeeModel] = []
            for totvs_employee in totvs_employees:
                if (
                    db_session.query(EmployeeModel)
                    .filter(EmployeeModel.code == totvs_employee.code)
                    .first()
                ):
                    continue

                role = (
                    db_session.query(EmployeeRoleModel)
                    .filter(EmployeeRoleModel.name == totvs_employee.role)
                    .first()
                )
                nationality = (
                    db_session.query(EmployeeNationalityModel)
                    .filter(EmployeeNationalityModel.description == totvs_employee.role)
                    .first()
                )
                marital_status = (
                    db_session.query(EmployeeMaritalStatusModel)
                    .filter(
                        EmployeeMaritalStatusModel.description == totvs_employee.role
                    )
                    .first()
                )
                gender = (
                    db_session.query(EmployeeGenderModel)
                    .filter(EmployeeGenderModel.description == totvs_employee.role)
                    .first()
                )

                dict_employee = {
                    **totvs_employee.model_dump(
                        exclude={"role", "nationality", "marital_status", "gender"}
                    ),
                    "role": role,
                    "nationality": nationality,
                    "marital_status": marital_status,
                    "gender": gender,
                }

                updates.append(EmployeeModel(**dict_employee))

            db_session.add_all(updates)
            db_session.commit()
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc

    def create_employee(
        self,
        data: NewEmployeeSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> EmployeeSerializerSchema:
        """Creates new employee"""
        if data.code and (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.code == data.code)
            .first()
        ):
            raise HTTPException(
                detail={"code": "Colaborador já existe"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if (
            db_session.query(EmployeeModel)
            .filter(
                EmployeeModel.taxpayer_identification == data.taxpayer_identification
            )
            .first()
        ):
            raise HTTPException(
                detail={"taxpayer_identification": "Colaborador já existe"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        (role, nationality, marital_status, gender) = self.__validate_nested(
            data, db_session
        )

        new_emplyoee = EmployeeModel(
            role=role,
            nationality=nationality,
            marital_status=marital_status,
            gender=gender,
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
        filter_list: str = None,
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

        if filter_list:
            employee_list = employee_list.join(EmployeeModel.role,).filter(
                or_(
                    EmployeeRoleModel.name.in_(filter_list),
                )
            )

            employee_list = employee_list.join(EmployeeModel.nationality,).filter(
                or_(
                    EmployeeNationalityModel.description.in_(filter_list),
                )
            )

            employee_list = employee_list.join(EmployeeModel.marital_status,).filter(
                or_(
                    EmployeeMaritalStatusModel.description.in_(filter_list),
                )
            )

            employee_list = employee_list.join(EmployeeModel.gender,).filter(
                or_(
                    EmployeeGenderModel.description.in_(filter_list),
                )
            )

        params = Params(page=page, size=size)
        paginated = paginate(
            employee_list,
            params=params,
            transformer=lambda employee_list: [
                self.serialize_employee(employee) for employee in employee_list
            ],
        )

        return paginated

    def update_marital_status_totvs(
        self,
        totvs_marital_status: List[EmployeeMatrimonialStatusTotvsSchema],
        db_session: Session,
    ):
        """Updates marital_status from totvs"""
        try:
            updates: List[EmployeeMaritalStatusModel] = []
            for totvs_marital_status_item in totvs_marital_status:
                db_marital_status = (
                    db_session.query(EmployeeMaritalStatusModel)
                    .filter(
                        EmployeeMaritalStatusModel.code
                        == totvs_marital_status_item.code
                    )
                    .first()
                )
                if db_marital_status:
                    db_marital_status.description = (
                        totvs_marital_status_item.description
                    )
                    updates.append(db_marital_status)
                    continue

                updates.append(
                    EmployeeMaritalStatusModel(**totvs_marital_status_item.model_dump())
                )

            db_session.add_all(updates)
            db_session.commit()

            logger.info(
                "Update Matrimonial Status from TOTVS. Total=%s", str(len(updates))
            )
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc

    def update_gender_totvs(
        self,
        totvs_gender: List[EmployeeGenderTotvsSchema],
        db_session: Session,
    ):
        """Updates gender from totvs"""
        try:
            updates: List[EmployeeGenderModel] = []
            for totvs_gender_item in totvs_gender:
                db_gender = (
                    db_session.query(EmployeeGenderModel)
                    .filter(EmployeeGenderModel.code == totvs_gender_item.code)
                    .first()
                )
                if db_gender:
                    db_gender.description = totvs_gender_item.description
                    updates.append(db_gender)
                    continue

                updates.append(EmployeeGenderModel(**totvs_gender_item.model_dump()))

            db_session.add_all(updates)
            db_session.commit()
            logger.info("Update Gender from TOTVS. Total=%s", str(len(updates)))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc

    def update_nationality_totvs(
        self,
        totvs_nationality: List[EmployeeNationalityTotvsSchema],
        db_session: Session,
    ):
        """Updates nationality from totvs"""
        try:
            updates: List[EmployeeNationalityModel] = []
            for totvs_nationality_item in totvs_nationality:
                db_nationality = (
                    db_session.query(EmployeeNationalityModel)
                    .filter(
                        EmployeeNationalityModel.code == totvs_nationality_item.code
                    )
                    .first()
                )
                if db_nationality:
                    db_nationality.description = totvs_nationality_item.description
                    updates.append(db_nationality)
                    continue

                updates.append(
                    EmployeeNationalityModel(**totvs_nationality_item.model_dump())
                )

            db_session.add_all(updates)
            db_session.commit()
            logger.info("Update Nationality from TOTVS. Total=%s", str(len(updates)))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc

    def update_role_totvs(
        self,
        totvs_role: List[EmployeeRoleTotvsSchema],
        db_session: Session,
    ):
        """Updates role from totvs"""
        try:
            updates: List[EmployeeRoleModel] = []
            for totvs_role_item in totvs_role:
                db_role = (
                    db_session.query(EmployeeRoleModel)
                    .filter(EmployeeRoleModel.code == totvs_role_item.code)
                    .first()
                )
                if db_role:
                    db_role.name = totvs_role_item.name
                    updates.append(db_role)
                    continue

                updates.append(EmployeeRoleModel(**totvs_role_item.model_dump()))

            db_session.add_all(updates)
            db_session.commit()
            logger.info("Update Role from TOTVS. Total=%s", str(len(updates)))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc
