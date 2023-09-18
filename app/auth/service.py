"""Auth service"""
import random
import string
import logging
from typing import Optional, List
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
)
from app.auth.models import UserModel, RoleModel, PermissionModel
from app.config import PASSWORD_SUPER_USER, PERMISSIONS
from app.database import Session_db

logger = logging.getLogger(__name__)


def get_password_hash(password: str) -> str:
    """Returns crypted password"""
    return bcrypt_context.hash(password)


def make_new_random_password() -> str:
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


def create_user(new_user: NewUserSchema, db_session: Session) -> UserSerializer:
    """Creates a new user"""
    role = db_session.query(RoleModel).filter(RoleModel.name == new_user.role).first()

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
        db_session.query(UserModel).filter(UserModel.email == new_user.email).first()
    )

    if user_test_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email alredy exist"
        )

    user_dict = {
        **new_user.model_dump(),
        "password": get_password_hash(make_new_random_password()),
    }
    user_dict["role_id"] = role.id
    del user_dict["role"]

    new_user_db = UserModel(**user_dict)
    db_session.add(new_user_db)
    db_session.commit()

    logger.info("New user add. %s", str(new_user_db))

    return serializer_user(new_user_db)


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
                password=get_password_hash(PASSWORD_SUPER_USER),
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
        for module, models in PERMISSIONS.items():
            perm = (
                db_session.query(PermissionModel)
                .filter(PermissionModel.module == module)
                .first()
            )
            if not perm:
                for model in models:
                    new_perm_view = PermissionModel(
                        module=module,
                        model=model,
                        method="view",
                    )
                    new_perm_edit = PermissionModel(
                        module=module, model=model, method="edit"
                    )
                    new_perm_add = PermissionModel(
                        module=module,
                        model=model,
                        method="add",
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


def get_users(
    db_session: Session,
    page: int = 1,
    size: int = 50,
    search: str = "",
    active: bool = True,
    staff: Optional[bool] = None,
) -> Page[UserSerializer]:
    """Get user list"""
    logger.debug(search)
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
        transformer=lambda user_list: [serializer_user(user) for user in user_list],
    )
    return paginated


def serializer_user(user: UserModel) -> UserSerializer:
    """Convert UserModel to UserSerializer"""
    permissions_serializer: List[PermissionSerializer] = []
    for perm in user.role.permissions:
        permissions_serializer.append(PermissionSerializer(**perm.__dict__))

    role_serializer = RoleSerializer(
        id=user.role.id,
        name=user.role.name,
        permissions=permissions_serializer,
    )

    return UserSerializer(
        id=user.id,
        role=role_serializer,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        taxpayer_identification=user.taxpayer_identification,
        is_active=user.is_active,
        is_staff=user.is_staff,
        last_login_in=user.last_login_in.isoformat(),
    )


def update_user(
    db_session: Session,
    user_id: int,
    data: UserUpdateSchema,
) -> UserSerializer:
    """Update user"""
    try:
        user = db_session.query(UserModel).filter(UserModel.id == user_id).first()
        is_updated = False

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if data.role:
            role = (
                db_session.query(RoleModel).filter(RoleModel.name == data.role).first()
            )
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
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
            user.password = get_password_hash(data.password)

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

        return serializer_user(user)
    except Exception as exc:
        msg = f"{exc.args[0]}"
        logger.warning("Could not update user. Error: %s", msg)
        db_session.close()
