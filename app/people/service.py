"""People service"""
from typing import List
import logging
from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.people.models import (
    EmployeeModel,
    EmployeeGenderModel,
    EmployeeMatrimonialStatusModel,
    EmployeeNationalityModel,
    EmployeeRoleModel,
)
from app.people.schemas import (
    EmployeeTotvsSchema,
    NewEmployeeSchema,
    EmployeeSerializer,
    EmployeeRoleSerializer,
    EmployeeNationalitySerializer,
    EmployeeGenderSerializer,
    EmployeeMatrimonialStatusSerializer,
    UpdateEmployeeSchema,
)

logger = logging.getLogger(__name__)


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
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )

        return employee

    def __validate_nested(self, data: NewEmployeeSchema, db_session: Session) -> tuple:
        """Validates role, nationality, matrimonial status and gender values"""
        if data.role:
            role = (
                db_session.query(EmployeeRoleModel)
                .filter(EmployeeRoleModel.name == data.role)
                .first()
            )
            if not role:
                raise HTTPException(
                    detail="Role does not extists",
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
                    detail="Nationatily does not extists",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.matrimonial_status:
            matrimonial_status = (
                db_session.query(EmployeeMatrimonialStatusModel)
                .filter(
                    EmployeeMatrimonialStatusModel.description
                    == data.matrimonial_status
                )
                .first()
            )
            if not matrimonial_status:
                raise HTTPException(
                    detail="Matrimonial status does not extists",
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
                    detail="Gender does not extists",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        return (role, nationality, matrimonial_status, gender)

    def serialize_employee(self, employee: EmployeeModel) -> EmployeeSerializer:
        """Serialize employee"""
        return EmployeeSerializer(
            id=employee.id,
            role=EmployeeRoleSerializer(**employee.role),
            nationality=EmployeeNationalitySerializer(**employee.nationality),
            matrimonial_status=EmployeeMatrimonialStatusSerializer(
                **employee.matrimonial_status
            ),
            gender=EmployeeGenderSerializer(**employee.gender),
            manager=employee.manager,
            address=employee.address,
            birthday=employee.birthday,
            cell_phone=employee.cell_phone,
            code=employee.code,
            email=employee.email,
            full_name=employee.full_name,
            legal_person=employee.legal_person,
            nacional_identification=employee.nacional_identification,
            taxpayer_identification=employee.taxpayer_identification,
        )

    def update_employees(
        self, totvs_employees: List[EmployeeTotvsSchema], db_session: Session
    ):
        """Updates employees"""
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
                matrimonial_status = (
                    db_session.query(EmployeeMatrimonialStatusModel)
                    .filter(
                        EmployeeMatrimonialStatusModel.description
                        == totvs_employee.role
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
                        exclude={"role", "nationality", "matrimonial_status", "gender"}
                    ),
                    "role": role,
                    "nationality": nationality,
                    "matrimonial_status": matrimonial_status,
                    "gender": gender,
                }

                updates.append(EmployeeModel(**dict_employee))

            db_session.add_all(updates)
            db_session.commit()
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc

    def create_employee(
        self, data: NewEmployeeSchema, db_session: Session
    ) -> EmployeeSerializer:
        """Creates new employee"""
        if (
            data.code
            and (
                db_session.query(EmployeeModel)
                .filter(EmployeeModel.code == data.code)
                .first()
            )
            or (
                db_session.query(EmployeeModel)
                .filter(
                    EmployeeModel.taxpayer_identification
                    == data.taxpayer_identification
                )
                .first()
            )
        ):
            raise HTTPException(
                detail="Employee already extists",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        (role, nationality, matrimonial_status, gender) = self.__validate_nested(
            data, db_session
        )

        new_emplyoee = EmployeeModel(
            role=role,
            nationality=nationality,
            matrimonial_status=matrimonial_status,
            gender=gender,
            code=data.code,
            full_name=data.full_name,
            taxpayer_identification=data.taxpayer_identification,
            nacional_identification=data.nacional_identification,
            address=data.address,
            cell_phone=data.cell_phone,
            email=data.email,
            birthday=data.birthday,
            manager=data.manager,
            legal_person=True,
        )
        db_session.add(new_emplyoee)
        db_session.commit()
        return self.serialize_employee(new_emplyoee)

    def update_employee(
        self, employee_id: int, data: UpdateEmployeeSchema, db_session: Session
    ) -> EmployeeSerializer:
        """Uptades new employee"""
        employee = self.__get_employee_or_404(employee_id, db_session)

        (role, nationality, matrimonial_status, gender) = self.__validate_nested(
            data, db_session
        )
        if data.role:
            employee.role = role
        if data.nationality:
            employee.nationality = nationality
        if data.matrimonial_status:
            employee.matrimonial_status = matrimonial_status
        if data.gender:
            employee.gender = gender
        if data.code:
            employee.code = data.code
        if data.full_name:
            employee.full_name = data.full_name
        if data.taxpayer_identification:
            employee.taxpayer_identification = data.taxpayer_identification
        if data.nacional_identification:
            employee.nacional_identification = data.nacional_identification
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
        return self.serialize_employee(employee)

    def get_employee(self, employee_id: int, db_session: Session) -> EmployeeSerializer:
        """Get an employee"""
        employee = self.__get_employee_or_404(employee_id, db_session)
        return self.serialize_employee(employee)

    def get_employees(
        self,
        db_session: Session,
        search: str = "",
        filter: str = None,
        page: int = 1,
        size: int = 50,
    ) -> Page[EmployeeSerializer]:
        """Get employees list"""

        employee_list = db_session.query(EmployeeModel).filter(
            or_(
                EmployeeModel.full_name.ilike(f"%{search}%"),
                EmployeeModel.email.ilike(f"%{search}"),
                EmployeeModel.nacional_identification.ilike(f"%{search}"),
                EmployeeModel.taxpayer_identification.ilike(f"%{search}"),
                EmployeeModel.cell_phone.ilike(f"%{search}"),
                EmployeeModel.manager.ilike(f"%{search}"),
                EmployeeModel.code.ilike(f"%{search}"),
            )
        )

        if filter:
            employee_list = employee_list.join(
                EmployeeModel.role,
            ).filter(
                or_(
                    EmployeeRoleModel.name == filter,
                )
            )

            employee_list = employee_list.join(
                EmployeeModel.nationality,
            ).filter(
                or_(
                    EmployeeNationalityModel.description == filter,
                )
            )

            employee_list = employee_list.join(
                EmployeeModel.matrimonial_status,
            ).filter(
                or_(
                    EmployeeMatrimonialStatusModel.description == filter,
                )
            )

            employee_list = employee_list.join(
                EmployeeModel.gender,
            ).filter(
                or_(
                    EmployeeGenderModel.description == filter,
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
