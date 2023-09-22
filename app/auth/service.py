"""Auth service"""
import random
import string
import logging
from typing import Optional, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi.exceptions import HTTPException
from fastapi import status
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate
from app.backends import bcrypt_context
from app.auth.schemas import (
    NewUserSchema,
    UserSerializer,
    PermissionSerializer,
    RoleSerializer,
    UserUpdateSchema,
    NewRoleSchema,
)
from app.auth.models import UserModel, RoleModel, PermissionModel
from app.config import PASSWORD_SUPER_USER, PERMISSIONS
from app.database import Session_db

logger = logging.getLogger(__name__)


ROLE_NOT_FOUND = "Role not found"


class UserSerivce:
    """User services"""

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
        return result_str

    def create_user(
        self, new_user: NewUserSchema, db_session: Session
    ) -> UserSerializer:
        """Creates a new user"""
        role = (
            db_session.query(RoleModel).filter(RoleModel.name == new_user.role).first()
        )

        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role"
            )

        user_test_username = (
            db_session.query(UserModel)
            .filter(UserModel.username == new_user.username)
            .first()
        )

        if user_test_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username alredy exist"
            )

        user_test_email = (
            db_session.query(UserModel)
            .filter(UserModel.email == new_user.email)
            .first()
        )

        if user_test_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email alredy exist"
            )

        user_dict = {
            **new_user.model_dump(),
            "password": self.get_password_hash(self.make_new_random_password()),
        }
        user_dict["role_id"] = role.id
        del user_dict["role"]

        new_user_db = UserModel(**user_dict)
        db_session.add(new_user_db)
        db_session.commit()

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
    ) -> Page[UserSerializer]:
        """Get user list"""
        if staff:
            user_list = db_session.query(UserModel).filter(
                or_(
                    UserModel.full_name.ilike(f"%{search}%"),
                    UserModel.email.ilike(f"%{search}"),
                    UserModel.username.ilike(f"%{search}"),
                    UserModel.taxpayer_identification.ilike(f"%{search}"),
                )
            )
            user_list.filter(UserModel.is_staff == staff)
        else:
            user_list = db_session.query(UserModel).filter(
                or_(
                    UserModel.full_name.ilike(f"%{search}%"),
                    UserModel.email.ilike(f"%{search}"),
                    UserModel.username.ilike(f"%{search}"),
                    UserModel.taxpayer_identification.ilike(f"%{search}"),
                )
            )

        user_list.filter(UserModel.is_active == active)

        params = Params(page=page, size=size)
        paginated = paginate(
            user_list,
            params=params,
            transformer=lambda user_list: [
                self.serialize_user(user) for user in user_list
            ],
        )
        return paginated

    def serialize_user(self, user: UserModel) -> UserSerializer:
        """Convert UserModel to UserSerializer"""
        return UserSerializer(
            id=user.id,
            role=RoleService().serialize_role(user.role),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            taxpayer_identification=user.taxpayer_identification,
            is_active=user.is_active,
            is_staff=user.is_staff,
            last_login_in=user.last_login_in.isoformat(),
        )

    def update_user(
        self,
        db_session: Session,
        user_id: int,
        data: UserUpdateSchema,
    ) -> Union[UserSerializer, None]:
        """Update user by id"""
        try:
            user = db_session.query(UserModel).filter(UserModel.id == user_id).first()
            is_updated = False

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            if data.role:
                role = (
                    db_session.query(RoleModel)
                    .filter(RoleModel.name == data.role)
                    .first()
                )
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail=ROLE_NOT_FOUND
                    )

                user.role = role

            if data.full_name:
                is_updated = True
                user.full_name = data.full_name

            if data.username:
                is_updated = True
                user.username = data.username

            if data.password:
                is_updated = True
                user.password = self.get_password_hash(data.password)

            if data.email:
                is_updated = True
                user.email = data.email

            if data.taxpayer_identification:
                is_updated = True
                user.taxpayer_identification = data.taxpayer_identification

            if data.is_active is not None:
                is_updated = True
                user.is_active = data.is_active

            if data.is_staff is not None:
                is_updated = True
                user.is_staff = data.is_staff

            if is_updated:
                db_session.add(user)
                db_session.commit()

            return self.serialize_user(user)

        except Exception as exc:
            msg = f"{exc.args[0]}"
            logger.warning("Could not update user. Error: %s", msg)
        return None

    def get_user(self, user_id: int, db_session: Session) -> UserSerializer:
        """Get user by id"""
        user = db_session.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return self.serialize_user(user)


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
                full_name="Solutis Agile Administrador",
                password=UserSerivce().get_password_hash(PASSWORD_SUPER_USER),
                email="admin@email.com",
                taxpayer_identification="00000000000000",
                is_staff=True,
            )
            db_session.add(new_super_user)
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
        logger.warning("Could not create super user. Error: %s", msg)
    finally:
        db_session.close_all()


class RoleService:
    """Role services"""

    def create_role(
        self, new_role: NewRoleSchema, db_session: Session
    ) -> RoleSerializer:
        """Creates a new role"""

        for id_perm in new_role.permissions:
            if (
                not db_session.query(PermissionModel)
                .filter(PermissionModel.id == id_perm)
                .first()
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Permission does not exists. {id_perm}",
                )

        role = (
            db_session.query(RoleModel).filter(RoleModel.name == new_role.name).first()
        )

        if role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Role alredy exists"
            )

        new_role_db = RoleModel(**new_role.model_dump(exclude="permissions"))
        db_session.add(new_role_db)
        db_session.commit()

        logger.info("New role add. %s", str(new_role_db))

        return self.serialize_role(new_role_db)

    def serialize_role(self, role: RoleModel) -> RoleSerializer:
        """Serialize role"""
        dict_role = role.__dict__
        serializer_permissions = []
        for perm in role.permissions:
            serializer_permissions.append(PermissionSerializer(**perm.__dict__))
        dict_role.update({"permissions": serializer_permissions})
        return RoleSerializer(**dict_role)

    def get_roles(
        self,
        db_session: Session,
        page: int = 1,
        size: int = 50,
        search: str = "",
    ) -> Page[RoleSerializer]:
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

    def update_role(
        self,
        db_session: Session,
        role_id: int,
        data: NewRoleSchema,
    ) -> Union[RoleSerializer, None]:
        """Update role by id"""
        try:
            role = db_session.query(RoleModel).filter(RoleModel.id == role_id).first()
            is_updated = False

            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=ROLE_NOT_FOUND
                )

            if data.name:
                is_updated = True
                role.name = data.name

            if data.permissions:
                is_updated = True

                # verifica novas inclusões
                for perm in data.permissions:
                    permission = (
                        db_session.query(PermissionModel)
                        .filter(PermissionModel.id == perm)
                        .first()
                    )
                    if not permission:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Permission not found. id={perm}",
                        )
                    try:
                        role.permissions.index(permission)
                    except ValueError:
                        role.permissions.append(permission)

                # verifica exclusão
                perms_to_remove: List[PermissionModel] = []
                for perm in role.permissions:
                    try:
                        data.permissions.index(permission.id)
                    except ValueError:
                        perms_to_remove.append(perm)
                for perm_to_remove in perms_to_remove:
                    role.permissions.remove(perm_to_remove)

            if is_updated:
                db_session.add(role)
                db_session.commit()

            return self.serialize_role(role)

        except Exception as exc:
            msg = f"{exc.args[0]}"
            logger.warning("Could not update role. Error: %s", msg)
        return None

    def get_role(self, role_id: int, db_session: Session) -> RoleSerializer:
        """Get role by id"""
        role = db_session.query(RoleModel).filter(RoleModel.id == role_id).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=ROLE_NOT_FOUND
            )

        return self.serialize_role(role)


class PermissionService:
    """Permission services"""

    def serialize_permission(self, permission: PermissionModel) -> PermissionSerializer:
        """Serialize permission"""
        return PermissionSerializer(**permission.__dict__)

    def get_permissions(
        self,
        db_session: Session,
        page: int = 1,
        size: int = 50,
        search: str = "",
    ) -> Page[PermissionSerializer]:
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
