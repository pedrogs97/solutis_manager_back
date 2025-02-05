"""Auth service"""

import logging
import random
import string
from typing import List, Union

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.auth.filters import GroupFilter, PermissionFilter, UserFilter
from src.auth.models import GroupModel, PermissionModel, UserModel
from src.auth.schemas import (
    GroupSerializerSchema,
    NewGroupSchema,
    NewPasswordSchema,
    NewUserSchema,
    PermissionSerializerSchema,
    UserChangePasswordSchema,
    UserListSerializerSchema,
    UserSerializerSchema,
    UserUpdateSchema,
)
from src.backends import Email365Client, bcrypt_context
from src.config import DEBUG, DEFAULT_DATE_FORMAT, PASSWORD_SUPER_USER, PERMISSIONS
from src.database import Session_db
from src.datasync.models import (
    EmployeeGenderTOTVSModel,
    EmployeeMaritalStatusTOTVSModel,
    EmployeeNationalityTOTVSModel,
)
from src.log.services import LogService
from src.people.models import EmployeeModel

logger = logging.getLogger(__name__)

service_log = LogService()


class UserSerivce:
    """User services"""

    def __get_user_or_404(self, user_id: int, db_session: Session) -> UserModel:
        """
        Retrieve a user from the database based on the provided user ID.

        If the user is not found, raise an HTTPException with a 404 status code and an error message.

        Args:
            user_id (int): The ID of the user to retrieve.
            db_session (Session): The database session object.

        Returns:
            UserModel: The retrieved user object if found.

        Raises:
            HTTPException: If the user is not found in the database.
        """
        user = db_session.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "userId", "error": "Usuário não encontrado"},
            )

        return user

    def get_password_hash(self, password: str) -> str:
        """
        Returns the hashed version of a given password using the bcrypt hashing algorithm.

        :param password: The password to be hashed.
        :type password: str
        :return: The hashed password.
        :rtype: str
        """
        return bcrypt_context.hash(password)

    def make_new_random_password(self) -> str:
        """
        Generate a new random password consisting of a combination of lowercase letters and digits.

        Returns:
            str: The randomly generated password.

        Example Usage:
            user_service = UserSerivce()

            new_password = user_service.make_new_random_password()

            print(new_password)

            # Output: 8aBcD3e
        """
        # choose from all lowercase letter
        letters = string.ascii_letters
        digits = string.digits
        result_str = ""
        for i in range(1, 8):
            rand = random.randint(1, 10)
            if rand % i != 0:
                result_str += "".join(random.choice(letters))
            else:
                result_str += "".join(random.choice(digits))

        if DEBUG:
            logger.debug("New pass. %s", result_str)

        return result_str

    def create_user(
        self,
        new_user: NewUserSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> UserSerializerSchema:
        """
        Creates a new user in the system.

        Args:
            new_user (NewUserSchema): The data for the new user, including the group ID, employee ID, username, and email.
            db_session (Session): The database session object.
            authenticated_user (UserModel): The authenticated user who is creating the new user.

        Returns:
            UserSerializerSchema: A serialized object representing the newly created user.

        Raises:
            HTTPException: If there are any errors in the input data, such as invalid group ID, invalid employee ID,
                duplicate username, or duplicate email. The exception will have a 400 status code and the corresponding
                error messages as the detail.
        """
        errors = []

        group = (
            db_session.query(GroupModel)
            .filter(GroupModel.id == new_user.group_id)
            .first()
        )

        if not group:
            errors.append({"field": "groupId", "error": "Perfil inválido"})

        employee = (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.id == new_user.employee_id)
            .first()
        )

        if not employee:
            errors.append({"field": "employeeId", "error": "Colaborador inválido"})

        if employee and employee.user:
            errors.append(
                {
                    "field": "employeeId",
                    "error": "Colaborador já está vinculado a um usuário",
                }
            )

        user_test_username = (
            db_session.query(UserModel)
            .filter(UserModel.username == new_user.username)
            .first()
        )

        if user_test_username:
            errors.append({"field": "username", "error": "Nome de usuário já existe"})

        user_test_email = (
            db_session.query(UserModel)
            .filter(UserModel.email == new_user.email)
            .first()
        )

        if user_test_email:
            errors.append({"field": "email", "error": "Já existe este e-mail"})

        if len(errors) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)

        password = self.make_new_random_password()
        user_dict = {
            **new_user.model_dump(),
            "password": self.get_password_hash(password),
        }

        user_dict["group_id"] = group.id
        user_dict["employee_id"] = employee.id

        new_user_db = UserModel(**user_dict)
        db_session.add(new_user_db)
        db_session.commit()
        db_session.flush()
        service_log.set_log(
            "auth",
            "user",
            "Criação de usuário",
            new_user_db.id,
            authenticated_user,
            db_session,
        )
        logger.info("New user add. %s", str(new_user_db))

        name = (
            new_user_db.employee.full_name
            if new_user_db.employee
            else new_user_db.username
        )
        mail_client = Email365Client(
            new_user_db.email,
            "Novo Usuário",
            "new_user",
            {
                "username": new_user_db.username,
                "password": password,
                "full_name": name,
            },
        )
        if mail_client.send_message():
            service_log.set_log(
                "auth",
                "user",
                "Envio de novo usuário",
                new_user_db.id,
                authenticated_user,
                db_session,
            )
        else:
            logger.warning("Não foi possível enviar o e-mail")

        return self.serialize_user(new_user_db)

    def get_users(
        self,
        db_session: Session,
        user_filters: UserFilter,
        employee_empty: bool = False,
        employee_not_empty: bool = False,
        page: int = 1,
        size: int = 50,
    ) -> Page[UserSerializerSchema]:
        """
        Get a paginated list of users based on the provided parameters.

        Args:
            db_session (Session): The database session object.
            user_filters (UserFilter): An instance of the `UserFilter` class used to filter the user list.
            page (int, optional): The page number of the paginated results. Defaults to 1.
            size (int, optional): The number of users per page. Defaults to 50.

        Returns:
            Page[UserSerializerSchema]: A `Page` object containing a paginated list of serialized user objects.
        """
        if employee_empty:
            user_list = (
                user_filters.filter(
                    db_session.query(UserModel)
                    .join(GroupModel)
                    .outerjoin(EmployeeModel),
                )
                .filter(UserModel.employee.is_(None))
                .order_by(desc(UserModel.id))
            )
        elif employee_not_empty:
            user_list = (
                user_filters.filter(
                    db_session.query(UserModel)
                    .join(GroupModel)
                    .outerjoin(EmployeeModel),
                )
                .filter(UserModel.employee.is_not(None))
                .order_by(desc(UserModel.id))
            )
        else:
            user_list = user_filters.filter(
                db_session.query(UserModel).join(GroupModel).outerjoin(EmployeeModel)
            ).order_by(desc(UserModel.id))

        params = Params(page=page, size=size)
        paginated = paginate(
            user_list,
            params=params,
            transformer=lambda user_list: [
                self.serialize_user(user, is_list=True).model_dump(by_alias=True)
                for user in user_list
            ],
        )
        return paginated

    def serialize_user(
        self, user: UserModel, is_list=False
    ) -> Union[UserSerializerSchema, UserListSerializerSchema]:
        """
        Convert UserModel to UserSerializerSchema or UserListSerializerSchema object.

        Args:
            user (UserModel): The UserModel object representing a user.
            is_list (bool, optional): Determines whether to use UserListSerializerSchema or UserSerializerSchema. Defaults to False.

        Returns:
            Union[UserSerializerSchema, UserListSerializerSchema]: The serialized user object.

        Example Usage:
            user = UserModel(...)
            serializer = UserService().serialize_user(user)
            print(serializer)
        """
        full_name: str = user.employee.full_name if user.employee else ""
        taxpayer_identification: str = (
            user.employee.taxpayer_identification if user.employee else ""
        )
        employee_id = user.employee.id if user.employee else None
        if is_list:
            return UserListSerializerSchema(
                id=user.id,
                group_id=user.group.id,
                group=user.group.name,
                username=user.username,
                full_name=full_name,
                taxpayer_identification=taxpayer_identification,
                email=user.email,
                is_active=user.is_active,
                is_staff=user.is_staff,
                last_login_in=(
                    user.last_login_in.strftime(DEFAULT_DATE_FORMAT)
                    if user.last_login_in
                    else None
                ),
                employee_id=employee_id,
                department=user.department,
                manager=user.manager,
            )
        return UserSerializerSchema(
            id=user.id,
            group=GroupService().serialize_group(user.group),
            username=user.username,
            full_name=full_name,
            taxpayer_identification=taxpayer_identification,
            email=user.email,
            is_active=user.is_active,
            is_staff=user.is_staff,
            last_login_in=(
                user.last_login_in.strftime(DEFAULT_DATE_FORMAT)
                if user.last_login_in
                else None
            ),
            employee_id=employee_id,
            department=user.department,
            manager=user.manager,
        )

    def update_user(
        self,
        db_session: Session,
        user_id: int,
        data: UserUpdateSchema,
        authenticated_user: UserModel,
    ) -> Union[UserSerializerSchema, None]:
        """
        Update the details of a user in the system.

        Args:
            db_session (Session): The database session object.
            user_id (int): The ID of the user to be updated.
            data (UserUpdateSchema): The updated data for the user, including the group ID, employee ID, username, email, is_active, and is_staff.
            authenticated_user (UserModel): The authenticated user who is performing the update.

        Returns:
            Union[UserSerializerSchema, None]: The serialized user object if the update is successful, None otherwise.

        Raises:
            HTTPException: If any errors occur during the update process, with a 400 status code and the corresponding error messages as the detail.
        """
        try:
            user = self.__get_user_or_404(user_id, db_session)
            errors = []
            is_updated = False

            if data.group_id and user.group.id != data.group_id:
                group = (
                    db_session.query(GroupModel)
                    .filter(GroupModel.id == data.group_id)
                    .first()
                )

                if not group:
                    errors.append(
                        {"field": "group", "error": "Perfil de usuário não encontrado"}
                    )
                else:
                    is_updated = True
                    user.group_id = group.id

            if data.employee_id and user.employee.id != data.employee_id:
                employee = (
                    db_session.query(EmployeeModel)
                    .filter(EmployeeModel.id == data.employee_id)
                    .first()
                )
                if not employee:
                    errors.append(
                        {"field": "employee", "error": "Colaborador não encontrado"}
                    )
                else:
                    is_updated = True
                    user.employee = employee

            if data.username and user.username != data.username:
                user_find = (
                    db_session.query(UserModel)
                    .filter(
                        UserModel.username == data.username, UserModel.id != user_id
                    )
                    .first()
                )

                if user_find:
                    errors.append(
                        {"field": "username", "error": "Nome de usuário já existe"}
                    )
                else:
                    is_updated = True
                    user.username = data.username

            if data.email and user.email != data.email:
                user_find = (
                    db_session.query(UserModel)
                    .filter(UserModel.email == data.email, UserModel.id != user_id)
                    .first()
                )

                if user_find:
                    errors.append({"field": "email", "error": "E-mail já existe"})
                else:
                    is_updated = True
                    user.email = data.email

            if data.is_active is not None and user.is_active != data.is_active:
                is_updated = True
                user.is_active = data.is_active

            if data.is_staff is not None and user.is_staff != data.is_staff:
                is_updated = True
                user.is_staff = data.is_staff

            if data.department is not None and user.department != data.department:
                is_updated = True
                user.department = data.department

            if data.manager is not None and user.manager != data.manager:
                is_updated = True
                user.manager = data.manager

            if len(errors) > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=errors
                )

            if is_updated:
                db_session.add(user)
                db_session.commit()

                service_log.set_log(
                    "auth",
                    "user",
                    "Edição de usuário",
                    user.id,
                    authenticated_user,
                    db_session,
                )
                logger.info("Updates user. %s", str(user))
        except HTTPException as http_exc:
            raise http_exc
        except Exception as exc:
            msg = f"{exc.args[0]}"
            logger.warning("Could not update user. Error: %s", msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": msg}
            ) from exc

        return self.serialize_user(user)

    def update_password(
        self,
        data: UserChangePasswordSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ):
        """
        Update the password of a user.

        Args:
            data (UserChangePasswordSchema): The data containing the current password and the new password.
            db_session (Session): The database session object.
            authenticated_user (UserModel): The authenticated user whose password is being updated.

        Raises:
            HTTPException: If the current password provided by the user does not match the hashed password stored in the database.

        Returns:
            None: This method does not return any output. It updates the password of the authenticated user in the database.
        """
        if not bcrypt_context.verify(
            data.current_password, authenticated_user.password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"field": "password", "error": "Senha atual inválida"},
            )

        authenticated_user.password = self.get_password_hash(data.password)
        db_session.add(authenticated_user)
        db_session.commit()

        service_log.set_log(
            "auth",
            "user",
            "Atualização de senha",
            authenticated_user.id,
            authenticated_user,
            db_session,
        )
        logger.info("Password updated. %s", str(authenticated_user))

    def get_user(self, user_id: int, db_session: Session) -> UserSerializerSchema:
        """
        Retrieve a user from the database based on the provided user ID and return a serialized representation of the user.

        Args:
            user_id (int): The ID of the user to retrieve.
            db_session (Session): The database session object.

        Returns:
            UserSerializerSchema: A serialized object representing the retrieved user.

        Raises:
            HTTPException: If the user is not found in the database.
        """
        user = self.__get_user_or_404(user_id, db_session)

        return self.serialize_user(user)

    def send_new_password(
        self,
        data: NewPasswordSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ):
        """
        Sends a new password to a user.

        Args:
            data (NewPasswordSchema): The data for sending a new password, including the user ID.
            db_session (Session): The database session object.
            authenticated_user (UserModel): The authenticated user who is sending the new password.

        Returns:
            None

        Raises:
            NotFoundError: If the user with the provided user ID is not found in the database.
        """

        user = self.__get_user_or_404(data.user_id, db_session)

        name = user.employee.full_name if user.employee else user.username
        new_pass = self.make_new_random_password()

        mail_client = Email365Client(
            user.email,
            "Nova senha",
            "new_password",
            {
                "username": user.username,
                "new_password": new_pass,
                "full_name": name,
            },
        )
        if mail_client.send_message():
            user.password = self.get_password_hash(new_pass)
            db_session.add(user)
            db_session.commit()
            service_log.set_log(
                "auth",
                "user",
                "Envio de nova senha",
                user.id,
                authenticated_user,
                db_session,
            )
        else:
            logger.warning("Não foi possível enviar o e-mail")


def create_super_user():
    """Creates super user"""
    try:
        db_session = Session_db()
        super_user = (
            db_session.query(UserModel)
            .filter(UserModel.username == "agile_admin")
            .first()
        )

        group_admin = (
            db_session.query(GroupModel).filter(GroupModel.name == "MASTER").first()
        )

        if not group_admin:
            group_admin = GroupModel(name="MASTER")
            db_session.add(group_admin)
            db_session.commit()
            db_session.flush()

        all_perms = db_session.query(PermissionModel).all()
        updated = False
        for perm in all_perms:
            found = False
            for group_perm in group_admin.permissions:
                if group_perm.id == perm.id:
                    found = True
                    break

            if not found:
                updated = True
                group_admin.permissions.append(perm)

        if updated:
            db_session.commit()
            db_session.flush()

        if not super_user:
            new_super_user = UserModel(
                username="agile_admin",
                group_id=group_admin.id,
                password=UserSerivce().get_password_hash(PASSWORD_SUPER_USER),
                email="admin@email.com",
                is_staff=True,
            )
            db_session.add(new_super_user)
            db_session.commit()
            db_session.flush()

        if super_user and not super_user.group:
            super_user.group = group_admin
            db_session.commit()

    except Exception as exc:
        msg = f"{exc.args[0]}"
        logger.warning("Could not create super user. Error: %s", msg)
    finally:
        db_session.close_all()


def create_permissions():
    """Creates base permissions"""
    try:
        db_session = Session_db()
        for module, dict_module in PERMISSIONS.items():
            for dict_model in dict_module["models"]:
                perm = (
                    db_session.query(PermissionModel)
                    .filter(PermissionModel.model == dict_model["name"])
                    .first()
                )
                if not perm:
                    module_label = dict_module["label"]
                    model_label = dict_model["label"]
                    new_perm_view = PermissionModel(
                        module=module,
                        model=dict_model["name"],
                        action="view",
                        description=f"Permissão de visualizar um(a) {model_label} no módulo {module_label}.",
                    )
                    new_perm_edit = PermissionModel(
                        module=module,
                        model=dict_model["name"],
                        action="edit",
                        description=f"Permissão de editar um(a) {model_label} no módulo {module_label}.",
                    )

                    new_perm_add = PermissionModel(
                        module=module,
                        model=dict_model["name"],
                        action="add",
                        description=f"Permissão de adicionar um(a) {model_label} no módulo {module_label}.",
                    )

                    new_perm_delete = PermissionModel(
                        module=module,
                        model=dict_model["name"],
                        action="delete",
                        description=f"Permissão de remover um(a) {model_label} no módulo {module_label}.",
                    )
                    new_permissions = [
                        new_perm_view,
                        new_perm_edit,
                        new_perm_add,
                        new_perm_delete,
                    ]
                    db_session.add_all(new_permissions)
        db_session.commit()
    except Exception as exc:
        msg = f"{exc.args[0]}"
        logger.warning("Could not create permissions. Error: %s", msg)
    finally:
        db_session.close_all()


def create_initial_data():
    """
    Create Nationalities
    """
    try:
        db_session = Session_db()
        nationality = (
            db_session.query(EmployeeNationalityTOTVSModel)
            .filter(EmployeeNationalityTOTVSModel.code == "BR")
            .first()
        )
        if not nationality:
            nationality = EmployeeNationalityTOTVSModel(code="BR", description="Brasil")
            db_session.add(nationality)
            db_session.commit()
            db_session.flush()

        marital_status = (
            db_session.query(EmployeeMaritalStatusTOTVSModel)
            .filter(EmployeeMaritalStatusTOTVSModel.code == "S")
            .first()
        )
        if not marital_status:
            marital_status = EmployeeMaritalStatusTOTVSModel(
                code="S", description="Solteiro(a)"
            )
            db_session.add(marital_status)
            db_session.commit()
            db_session.flush()

        gender = (
            db_session.query(EmployeeGenderTOTVSModel)
            .filter(EmployeeGenderTOTVSModel.code == "M")
            .first()
        )
        if not gender:
            gender = EmployeeGenderTOTVSModel(code="M", description="Masculino")
            db_session.add(gender)
            db_session.commit()
            db_session.flush()

        employee_test = (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.email == "test@gmail.com")
            .first()
        )
        if not employee_test:
            employee = EmployeeModel(
                role=None,  # It comes from TOTVS
                nationality=nationality,
                marital_status=marital_status,
                gender=gender,
                code="0001",
                full_name="Employee Test",
                taxpayer_identification="00000000000",
                national_identification="0000000000",
                address="Rua da esquina, 31, Alpha Vile, Salvador",
                cell_phone="71999999999",
                email="test@gmail.com",
                birthday="1990-01-01",
                manager="Joao da Silva",
                legal_person=False,
            )
            db_session.add(employee)
            db_session.flush()
            db_session.commit()

    except Exception as exc:
        msg = f"{exc.args[0]}"
        logger.warning("Could not create initial data. Error: %s", msg)
    finally:
        db_session.close_all()


class GroupService:
    """group services"""

    def __get_group_or_404(self, group_id: int, db_session: Session) -> GroupModel:
        """
        Get a group from the database based on the provided group_id and raise a 404 HTTPException if the group is not found.

        Args:
            group_id (int): The ID of the group to retrieve.
            db_session (Session): The SQLAlchemy database session.

        Returns:
            GroupModel: The retrieved group from the database.

        Raises:
            HTTPException: If the group with the specified ID is not found.
        """
        group = db_session.query(GroupModel).filter(GroupModel.id == group_id).first()

        if not group:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "name", "errror": "Perfil de usuário não encontrado"},
            )

        return group

    def create_group(
        self,
        new_group: NewGroupSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> GroupSerializerSchema:
        """
        Creates a new group in the database.

        Args:
            new_group (NewGroupSchema): The details of the new group to be created.
            db_session (Session): The SQLAlchemy database session.
            authenticated_user (UserModel): The authenticated user who is creating the group.

        Returns:
            GroupSerializerSchema: The serialized representation of the created group.

        Raises:
            HTTPException: If there are any errors during the group creation process.

        """
        errors = []
        ids_not_found = []
        for id_perm in new_group.permissions:
            if (
                not db_session.query(PermissionModel)
                .filter(PermissionModel.id == id_perm)
                .first()
            ):
                ids_not_found.append(id_perm)

        if len(ids_not_found) > 0:
            errors.append(
                {
                    "field": "permissions",
                    "error": {
                        "error": "Permissões não existem",
                        "items": ids_not_found,
                    },
                }
            )

        group = (
            db_session.query(GroupModel)
            .filter(GroupModel.name == new_group.name)
            .first()
        )

        if group:
            errors.append({"field": "name", "error": "Perfil de usuário já existe"})

        if len(errors) > 0:
            db_session.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=errors,
            )

        permissions = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.id.in_(new_group.permissions))
            .all()
        )

        new_group_db = GroupModel(**new_group.model_dump(exclude="permissions"))
        new_group_db.permissions = permissions
        db_session.add(new_group_db)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "auth",
            "user",
            "Criação de perfil de usuário",
            new_group_db.id,
            authenticated_user,
            db_session,
        )
        logger.info("New group add. %s", str(new_group_db))

        return self.serialize_group(new_group_db)

    def serialize_group(self, group: GroupModel) -> GroupSerializerSchema:
        """Serialize group"""
        dict_group = group.__dict__
        serializer_permissions = []
        for perm in group.permissions:
            serializer_permissions.append(PermissionSerializerSchema(**perm.__dict__))
        dict_group.update({"permissions": serializer_permissions})
        return GroupSerializerSchema(**dict_group)

    def get_groups(
        self,
        db_session: Session,
        group_filter: GroupFilter,
        page: int = 1,
        size: int = 50,
        fields: str = "",
    ) -> Page[GroupSerializerSchema]:
        """Get group list"""
        group_list = group_filter.filter(db_session.query(GroupModel)).order_by(
            desc(GroupModel.id)
        )

        params = Params(page=page, size=size)
        if fields == "":
            paginated = paginate(
                group_list,
                params=params,
                transformer=lambda group_list: [
                    self.serialize_group(group).model_dump(by_alias=True)
                    for group in group_list
                ],
            )
        else:
            list_fields = fields.split(",")
            paginated = paginate(
                group_list,
                params=params,
                transformer=lambda group_list: [
                    self.serialize_group(group).model_dump(
                        include={*list_fields}, by_alias=True
                    )
                    for group in group_list
                ],
            )
        return paginated

    def __check_new_perms(
        self,
        new_permissions: List[int],
        current_permissions: List[PermissionModel],
        db_session: Session,
    ):
        """Verify new perms"""
        ids_not_found = []
        for perm in new_permissions:
            permission = (
                db_session.query(PermissionModel)
                .filter(PermissionModel.id == perm)
                .first()
            )
            if not permission:
                ids_not_found.append(perm)
            try:
                current_permissions.index(permission)
            except ValueError:
                current_permissions.append(permission)

        if len(ids_not_found) > 0:
            db_session.close()
            errors = {"permissions": {"Permissões não encontradas": ids_not_found}}
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=errors,
            )

    def __check_remove_perms(
        self, new_permissions: List[int], current_permissions: List[PermissionModel]
    ):
        """Verify if needs remove perms"""
        perms_to_remove: List[PermissionModel] = []
        for perm in current_permissions:
            try:
                new_permissions.index(perm.id)
            except ValueError:
                perms_to_remove.append(perm)
        for perm_to_remove in perms_to_remove:
            current_permissions.remove(perm_to_remove)

    def update_group(
        self,
        db_session: Session,
        group_id: int,
        data: NewGroupSchema,
        authenticated_user: UserModel,
    ) -> Union[GroupSerializerSchema, None]:
        """Update group by id"""
        try:
            is_updated = False
            group = self.__get_group_or_404(group_id, db_session)

            if data.name and group.name != data.name:
                is_updated = True
                group.name = data.name

            if data.permissions:
                is_updated = True

                # verifica novas inclusões
                self.__check_new_perms(data.permissions, group.permissions, db_session)

                # verifica exclusão
                self.__check_remove_perms(data.permissions, group.permissions)

            if is_updated:
                db_session.add(group)
                db_session.commit()

                service_log.set_log(
                    "auth",
                    "user",
                    "Criação de usuário",
                    group.id,
                    authenticated_user,
                    db_session,
                )
                logger.info("Updates group. %s", str(group))
            return self.serialize_group(group)

        except HTTPException as http_exc:
            db_session.close()
            raise http_exc
        except Exception as exc:
            db_session.close()
            msg = f"{exc.args[0]}"
            logger.warning("Could not update group. Error: %s", msg)
        return self.serialize_group(group)

    def get_group(self, group_id: int, db_session: Session) -> GroupSerializerSchema:
        """Get group by id"""
        group = self.__get_group_or_404(group_id, db_session)
        return self.serialize_group(group)


class PermissionService:
    """Permission services"""

    def serialize_permission(
        self, permission: PermissionModel
    ) -> PermissionSerializerSchema:
        """Serialize permission"""
        return PermissionSerializerSchema(**permission.__dict__)

    def get_permissions(
        self,
        db_session: Session,
        permission_filter: PermissionFilter,
    ) -> Page[PermissionSerializerSchema]:
        """Get permission list"""
        permission_list = permission_filter.filter(
            db_session.query(PermissionModel)
        ).order_by(desc(PermissionModel.id))

        return [
            self.serialize_permission(permission).model_dump(by_alias=True)
            for permission in permission_list
        ]
