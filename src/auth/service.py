"""Auth service"""
import logging
import random
import string
from typing import List, Optional, Union

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_
from sqlalchemy.orm import Session

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
from src.backends import bcrypt_context
from src.config import DEBUG, DEFAULT_DATE_FORMAT, PASSWORD_SUPER_USER, PERMISSIONS
from src.database import Session_db
from src.log.services import LogService
from src.people.models import (
    EmployeeGenderModel,
    EmployeeMaritalStatusModel,
    EmployeeModel,
    EmployeeNationalityModel,
)

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
            if rand % i != 0 or i % rand != 0:
                result_str = "".join(random.choice(letters))
            else:
                result_str = "".join(random.choice(digits))

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
        group = (
            db_session.query(GroupModel)
            .filter(GroupModel.id == new_user.group_id)
            .first()
        )

        errors = {}

        if not group:
            errors.update({"field": "groupId", "error": "Perfil inválido"})

        employee = (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.id == new_user.employee_id)
            .first()
        )

        if not employee:
            errors.update({"field": "employeeId", "error": "Colaborador inválido"})

        user_test_username = (
            db_session.query(UserModel)
            .filter(UserModel.username == new_user.username)
            .first()
        )

        if user_test_username:
            errors.update({"field": "username", "error": "Nome de usuário já existe"})

        user_test_email = (
            db_session.query(UserModel)
            .filter(UserModel.email == new_user.email)
            .first()
        )

        if user_test_email:
            errors.update({"field": "email", "error": "Já existe este e-mail"})

        if len(errors.keys()) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)

        user_dict = {
            **new_user.model_dump(),
            "password": self.get_password_hash(self.make_new_random_password()),
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

        return self.serialize_user(new_user_db)

    def get_users(
        self,
        db_session: Session,
        page: int = 1,
        size: int = 50,
        search: str = "",
        active: bool = True,
        staff: Optional[bool] = None,
    ) -> Page[UserSerializerSchema]:
        """
        Get a paginated list of users based on the provided parameters.

        Args:
            db_session (Session): A SQLAlchemy session object for database operations.
            page (int, optional): The page number of the user list to retrieve. Default is 1.
            size (int, optional): The number of users to retrieve per page. Default is 50.
            search (str, optional): A search string to filter the user list by. Default is an empty string.
            active (bool, optional): A boolean value indicating whether to retrieve only active users. Default is True.
            staff (bool, optional): A boolean value indicating whether to retrieve only users who are staff members. Default is None.

        Returns:
            Page[UserSerializerSchema]: A paginated result of the user list, where each user is represented by an instance of the UserSerializerSchema class.
        """
        user_list = db_session.query(UserModel)

        if staff:
            user_list = user_list.filter(UserModel.is_staff == staff)

        if search != "":
            user_list = user_list.join(EmployeeModel).filter(
                or_(
                    EmployeeModel.full_name.ilike(f"%{search}%"),
                    UserModel.email.ilike(f"%{search}"),
                    UserModel.username.ilike(f"%{search}"),
                    EmployeeModel.taxpayer_identification.ilike(f"%{search}"),
                )
            )

        user_list = user_list.filter(UserModel.is_active == active)

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
        """Convert UserModel to UserSerializerSchema"""
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
                last_login_in=user.last_login_in.strftime(DEFAULT_DATE_FORMAT)
                if user.last_login_in
                else None,
                employee_id=employee_id,
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
            last_login_in=user.last_login_in.strftime(DEFAULT_DATE_FORMAT)
            if user.last_login_in
            else None,
            employee_id=employee_id,
        )

    def update_user(
        self,
        db_session: Session,
        user_id: int,
        data: UserUpdateSchema,
        authenticated_user: UserModel,
    ) -> Union[UserSerializerSchema, None]:
        """Update user by id"""
        try:
            user = self.__get_user_or_404(user_id, db_session)
            errors = []
            if data.group_id:
                group = (
                    db_session.query(GroupModel)
                    .filter(GroupModel.id == data.group_id)
                    .first()
                )
                if not group:
                    errors.append(
                        {"field": "group", "error": "Perfil de usuário não encontrado"}
                    )

                user.group_id = group.id

            if data.employee_id:
                employee = (
                    db_session.query(EmployeeModel)
                    .filter(EmployeeModel.id == data.employee_id)
                    .first()
                )
                if not employee:
                    errors.append(
                        {"field": "employee", "error": "Colaborador não encontrado"}
                    )

                user.employee = employee

            if data.username:
                employee = (
                    db_session.query(UserModel)
                    .filter(
                        UserModel.username == data.username, UserModel.id != user_id
                    )
                    .first()
                )
                if employee:
                    errors.append(
                        {"field": "username", "error": "Nome de usuário já existe"}
                    )
                is_updated = True
                user.username = data.username

            if data.email:
                employee = (
                    db_session.query(UserModel)
                    .filter(UserModel.email == data.email, UserModel.id != user_id)
                    .first()
                )
                if employee:
                    errors.append({"field": "email", "error": "E-mail já existe"})
                is_updated = True
                user.email = data.email

            if data.is_active is not None:
                is_updated = True
                user.is_active = data.is_active

            if data.is_staff is not None:
                is_updated = True
                user.is_staff = data.is_staff

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
                status_code=status.HTTP_400_BAD_REQUEST, detail={"error": msg}
            )

        return self.serialize_user(user)

    def update_password(
        self,
        data: UserChangePasswordSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ):
        """Update user password"""
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
        """Get user by id"""
        user = self.__get_user_or_404(user_id, db_session)

        return self.serialize_user(user)

    def send_new_password(
        self,
        data: NewPasswordSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ):
        """Sends new password"""

        user = self.__get_user_or_404(data.user_id, db_session)

        service_log.set_log(
            "auth",
            "user",
            "Envio de nova senha",
            user.id,
            authenticated_user,
            db_session,
        )

        # TODO serviço de envio de e-mail


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
            db_session.query(GroupModel)
            .filter(GroupModel.name == "Administrador")
            .first()
        )

        if not group_admin:
            group_admin = GroupModel(name="Administrador")
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

        if not super_user.group:
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
                    db_session.add(new_perm_view)
                    db_session.add(new_perm_edit)
                    db_session.add(new_perm_add)
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
            db_session.query(EmployeeNationalityModel)
            .filter(EmployeeNationalityModel.code == "BR")
            .first()
        )
        if not nationality:
            nationality = EmployeeNationalityModel(code="BR", description="Brasil")
            db_session.add(nationality)
            db_session.commit()
            db_session.flush()

        marital_status = (
            db_session.query(EmployeeMaritalStatusModel)
            .filter(EmployeeMaritalStatusModel.code == "S")
            .first()
        )
        if not marital_status:
            marital_status = EmployeeMaritalStatusModel(
                code="S", description="Solteiro(a)"
            )
            db_session.add(marital_status)
            db_session.commit()
            db_session.flush()

        gender = (
            db_session.query(EmployeeGenderModel)
            .filter(EmployeeGenderModel.code == "M")
            .first()
        )
        if not gender:
            gender = EmployeeGenderModel(code="M", description="Masculino")
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
                group=None,  # It comes from TOTVS
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
        """Get group or raise 404"""
        group = db_session.query(GroupModel).filter(GroupModel.id == group_id).first()

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "group", "errror": "Perfil de usuário não encontrado"},
            )

        return group

    def create_group(
        self,
        new_group: NewGroupSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> GroupSerializerSchema:
        """Creates a new group"""
        errors = {}
        ids_not_found = []
        for id_perm in new_group.permissions:
            if (
                not db_session.query(PermissionModel)
                .filter(PermissionModel.id == id_perm)
                .first()
            ):
                ids_not_found.append(id_perm)

        errors.update(
            {
                "field": "permissions",
                "error": {"error": "Permissões não existem", "items": ids_not_found},
            }
        )

        group = (
            db_session.query(GroupModel)
            .filter(GroupModel.name == new_group.name)
            .first()
        )

        permissions = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.id.in_(new_group.permissions))
            .all()
        )

        if group:
            errors.update({"field": "group", "error": "Perfil de usuário já existe"})

        if len(errors.keys()) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=errors,
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
        page: int = 1,
        size: int = 50,
        search: str = "",
        fields: str = "",
    ) -> Page[GroupSerializerSchema]:
        """Get group list"""
        group_list = db_session.query(GroupModel).filter(
            GroupModel.name.ilike(f"%{search}%")
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

            if data.name:
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
            raise http_exc
        except Exception as exc:
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
        page: int = 1,
        size: int = 50,
        search: str = "",
    ) -> Page[PermissionSerializerSchema]:
        """Get permission list"""
        permission_list = db_session.query(PermissionModel).filter(
            or_(
                PermissionModel.module.ilike(f"%{search}%"),
                PermissionModel.model.ilike(f"%{search}%"),
                PermissionModel.action.ilike(f"%{search}%"),
            )
        )

        params = Params(page=page, size=size)
        paginated = paginate(
            permission_list,
            params=params,
            transformer=lambda permission_list: [
                self.serialize_permission(permission) for permission in permission_list
            ],
        )
        return paginated
