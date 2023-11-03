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

from src.auth.models import PermissionModel, RoleModel, UserModel
from src.auth.schemas import (
    NewPasswordSchema,
    NewRoleSchema,
    NewUserSchema,
    PermissionSerializerSchema,
    RoleSerializerSchema,
    UserChangePasswordSchema,
    UserSerializerSchema,
    UserUpdateSchema,
)
from src.backends import bcrypt_context
from src.config import DEBUG, PASSWORD_SUPER_USER, PERMISSIONS
from src.database import Session_db
from src.log.services import LogService
from src.people.models import EmployeeModel

logger = logging.getLogger(__name__)

service_log = LogService()


class UserSerivce:
    """User services"""

    def __get_user_or_404(self, user_id: int, db_session: Session) -> UserModel:
        """Get user or rais not found"""
        user = db_session.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado"
            )

        return user

    def get_password_hash(self, password: str) -> str:
        """Returns crypted password"""
        return bcrypt_context.hash(password)

    def make_new_random_password(self) -> str:
        """Make new random password"""
        # choose from all lowercase letter
        letters = string.ascii_letters
        digits = string.digits
        result_str = ""
        for i in range(8):
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
        """Creates a new user"""
        role = (
            db_session.query(RoleModel).filter(RoleModel.name == new_user.role).first()
        )

        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Perfil inválido"
            )

        employee = (
            db_session.query(EmployeeModel)
            .filter(EmployeeModel.id == new_user.employee_id)
            .first()
        )

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Colaborador inválido"
            )

        user_test_username = (
            db_session.query(UserModel)
            .filter(UserModel.username == new_user.username)
            .first()
        )

        if user_test_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome de usuário já existe",
            )

        user_test_email = (
            db_session.query(UserModel)
            .filter(UserModel.email == new_user.email)
            .first()
        )

        if user_test_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe este e-mail"
            )

        user_dict = {
            **new_user.model_dump(),
            "password": self.get_password_hash(self.make_new_random_password()),
        }

        user_dict["role_id"] = role.id
        del user_dict["role"]
        user_dict["employee_id"] = employee.id

        new_user_db = UserModel(**user_dict)
        db_session.add(new_user_db)
        db_session.commit()
        db_session.flush()
        service_log.set_log(
            "auth", "user", "Criação de usuário", new_user_db.id, authenticated_user
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
        """Get user list"""
        if staff:
            user_list = (
                db_session.query(UserModel)
                .join(EmployeeModel)
                .filter(
                    or_(
                        EmployeeModel.full_name.ilike(f"%{search}%"),
                        UserModel.email.ilike(f"%{search}"),
                        UserModel.username.ilike(f"%{search}"),
                        EmployeeModel.taxpayer_identification.ilike(f"%{search}"),
                    )
                )
            )
            user_list = user_list.filter(UserModel.is_staff == staff)
        else:
            user_list = (
                db_session.query(UserModel)
                .join(EmployeeModel)
                .filter(
                    or_(
                        EmployeeModel.full_name.ilike(f"%{search}%"),
                        UserModel.email.ilike(f"%{search}"),
                        UserModel.username.ilike(f"%{search}"),
                        EmployeeModel.taxpayer_identification.ilike(f"%{search}"),
                    )
                )
            )

        user_list = user_list.filter(UserModel.is_active == active)

        params = Params(page=page, size=size)
        paginated = paginate(
            user_list,
            params=params,
            transformer=lambda user_list: [
                self.serialize_user(user) for user in user_list
            ],
        )
        return paginated

    def serialize_user(self, user: UserModel) -> UserSerializerSchema:
        """Convert UserModel to UserSerializerSchema"""
        full_name = (user.employee.full_name if user.employee else "",)
        taxpayer_identification = (
            user.employee.taxpayer_identification if user.employee else "",
        )
        return UserSerializerSchema(
            id=user.id,
            role=RoleService().serialize_role(user.role),
            username=user.username,
            full_name=full_name,
            taxpayer_identification=taxpayer_identification,
            email=user.email,
            is_active=user.is_active,
            is_staff=user.is_staff,
            last_login_in=user.last_login_in.strftime("%d/%m/%Y"),
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

            if data.role:
                role = (
                    db_session.query(RoleModel)
                    .filter(RoleModel.name == data.role)
                    .first()
                )
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Perfil de usuário não encontrado",
                    )

                user.role = role

            if data.employee_id:
                employee = (
                    db_session.query(EmployeeModel)
                    .filter(EmployeeModel.id == data.employee_id)
                    .first()
                )
                if not employee:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Colaborador não encontrado",
                    )

                user.employee = employee

            if data.username:
                is_updated = True
                user.username = data.username

            if data.email:
                is_updated = True
                user.email = data.email

            if data.is_active is not None:
                is_updated = True
                user.is_active = data.is_active

            if data.is_staff is not None:
                is_updated = True
                user.is_staff = data.is_staff

            if is_updated:
                db_session.add(user)
                db_session.commit()

                service_log.set_log(
                    "auth", "user", "Edição de usuário", user.id, authenticated_user
                )
                logger.info("Updates user. %s", str(user))

            return self.serialize_user(user)

        except Exception as exc:
            msg = f"{exc.args[0]}"
            logger.warning("Could not update user. Error: %s", msg)
        return None

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
                detail="Senha atual inválida",
            )

        authenticated_user.password = self.get_password_hash(data.password)
        db_session.add(authenticated_user)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "auth",
            "user",
            "Atualização de senha",
            authenticated_user.id,
            authenticated_user,
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
            "auth", "user", "Envio de nova senha", user.id, authenticated_user
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

        role_admin = (
            db_session.query(RoleModel)
            .filter(RoleModel.name == "Administrador")
            .first()
        )

        if not role_admin:
            role_admin = RoleModel(name="Administrador")
            db_session.add(role_admin)
            db_session.commit()

        if not super_user:
            new_super_user = UserModel(
                username="agile_admin",
                role_id=role_admin.id,
                password=UserSerivce().get_password_hash(PASSWORD_SUPER_USER),
                email="admin@email.com",
                is_staff=True,
            )
            db_session.add(new_super_user)
            db_session.commit()
    except Exception as exc:
        msg = f"{exc.args[0]}"
        print(f"Could not create super user. Error: {msg}")
        logger.warning("Could not create super user. Error: %s", msg)
    finally:
        db_session.close_all()


def create_permissions():
    """Creates base permissions"""
    try:
        db_session = Session_db()
        for module, dict_module in PERMISSIONS.items():
            perm = (
                db_session.query(PermissionModel)
                .filter(PermissionModel.module == module)
                .first()
            )
            if not perm:
                module_label = dict_module["label"]
                for dict_model in dict_module["models"]:
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


class RoleService:
    """Role services"""

    def __get_role_or_404(self, role_id: int, db_session: Session) -> RoleModel:
        """Get role or raise 404"""
        role = db_session.query(RoleModel).filter(RoleModel.id == role_id).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de usuário não encontrado",
            )

        return role

    def create_role(
        self,
        new_role: NewRoleSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> RoleSerializerSchema:
        """Creates a new role"""

        for id_perm in new_role.permissions:
            if (
                not db_session.query(PermissionModel)
                .filter(PermissionModel.id == id_perm)
                .first()
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Permissão não existe. {id_perm}",
                )

        role = (
            db_session.query(RoleModel).filter(RoleModel.name == new_role.name).first()
        )

        if role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Perfil de usuário já existe",
            )

        new_role_db = RoleModel(**new_role.model_dump(exclude="permissions"))
        db_session.add(new_role_db)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "auth",
            "user",
            "Criação de perfil de usuário",
            new_role_db.id,
            authenticated_user,
        )
        logger.info("New role add. %s", str(new_role_db))

        return self.serialize_role(new_role_db)

    def serialize_role(self, role: RoleModel) -> RoleSerializerSchema:
        """Serialize role"""
        dict_role = role.__dict__
        serializer_permissions = []
        for perm in role.permissions:
            serializer_permissions.append(PermissionSerializerSchema(**perm.__dict__))
        dict_role.update({"permissions": serializer_permissions})
        return RoleSerializerSchema(**dict_role)

    def get_roles(
        self,
        db_session: Session,
        page: int = 1,
        size: int = 50,
        search: str = "",
    ) -> Page[RoleSerializerSchema]:
        """Get role list"""
        role_list = db_session.query(RoleModel).filter(
            RoleModel.name.ilike(f"%{search}%")
        )

        params = Params(page=page, size=size)
        paginated = paginate(
            role_list,
            params=params,
            transformer=lambda role_list: [
                self.serialize_role(role) for role in role_list
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
        for perm in new_permissions:
            permission = (
                db_session.query(PermissionModel)
                .filter(PermissionModel.id == perm)
                .first()
            )
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Permissão não encontrada. id={perm}",
                )
            try:
                current_permissions.index(permission)
            except ValueError:
                current_permissions.append(permission)

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

    def update_role(
        self,
        db_session: Session,
        role_id: int,
        data: NewRoleSchema,
        authenticated_user: UserModel,
    ) -> Union[RoleSerializerSchema, None]:
        """Update role by id"""
        try:
            is_updated = False
            role = self.__get_role_or_404(role_id, db_session)

            if data.name:
                is_updated = True
                role.name = data.name

            if data.permissions:
                is_updated = True

                # verifica novas inclusões
                self.__check_new_perms(data.permissions, role.permissions, db_session)

                # verifica exclusão
                self.__check_remove_perms(data.permissions, role.permissions)

            if is_updated:
                db_session.add(role)
                db_session.commit()

                service_log.set_log(
                    "auth", "user", "Criação de usuário", role.id, authenticated_user
                )
                logger.info("Updates role. %s", str(role))
            return self.serialize_role(role)

        except Exception as exc:
            msg = f"{exc.args[0]}"
            logger.warning("Could not update role. Error: %s", msg)
        return None

    def get_role(self, role_id: int, db_session: Session) -> RoleSerializerSchema:
        """Get role by id"""
        role = self.__get_role_or_404(role_id, db_session)
        return self.serialize_role(role)


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
