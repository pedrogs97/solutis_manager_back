"""Base backends"""
import logging
from typing import Union, Annotated
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.auth.models import UserModel, TokenModel
from app.auth.schemas import PermissionSchema
from app.database import Session_db
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS
from app.exceptions import get_user_exception, token_exception

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

logger = logging.Logger(__name__)


def get_db_session():
    """Return session"""
    try:
        database = Session_db()
        yield database
    finally:
        database.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Returns if password is valid"""
    return bcrypt_context.verify(plain_password, hashed_password)


def get_user(
    username: str, password: str, db_session: Session
) -> Union[UserModel, None]:
    """Returns authenticated user if exists"""
    user = db_session.query(UserModel).filter(UserModel.username == username).first()

    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def logout_user(token: str, db_session: Session) -> None:
    """Logouts user"""
    user = get_current_user(token, db_session)
    old_token = (
        db_session.query(TokenModel).filter(TokenModel.user_id == user.id).first()
    )

    if not old_token:
        raise token_exception()

    db_session.delete(old_token)
    db_session.commit()


def get_user_token(user: UserModel, db_session: Session) -> dict:
    """Returns user token"""

    user.last_login_in = datetime.utcnow()
    db_session.add(user)
    db_session.commit()

    old_token = (
        db_session.query(TokenModel).filter(TokenModel.user_id == user.id).first()
    )

    permissions = [
        f"{perm.module}_{perm.model}_{perm.action}" for perm in user.role.permissions
    ]

    if not is_valid_token(old_token):
        encode = {"username": user.username, "id": user.id, "role": str(user.role)}
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        encode.update({"expires": expire.strftime("%d/%m/%Y")})
        token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

        token_db = TokenModel(user=user, token=token, expires_in=expire)
        db_session.add(token_db)
        db_session.commit()

        return {
            "role": user.role.name,
            "email": user.email,
            "full_name": user.full_name,
            "token": token,
            "permissions": permissions,
        }

    return {
        "role": user.role.name,
        "email": user.email,
        "full_name": user.full_name,
        "token": old_token.token,
        "permissions": permissions,
    }


def get_current_user(token: str, db_session: Session) -> UserModel:
    """Returns current user from token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        user_id: int = payload.get("id")
        role: int = payload.get("id")
        if username is None or user_id is None or role is None:
            raise get_user_exception()

        user_db = (
            db_session.query(UserModel)
            .filter(UserModel.id == user_id, UserModel.username == username)
            .first()
        )

        if not user_db:
            raise get_user_exception()

        return user_db
    except JWTError as exc:
        raise get_user_exception() from exc


def is_valid_token(token_obj: TokenModel) -> bool:
    """Verifies token validity"""
    if not token_obj:
        return False
    return token_obj.expires_in < datetime.utcnow()


class PermissionChecker:
    """Dependence class for check permissions"""

    def __init__(self, required_permissions: PermissionSchema) -> None:
        self.required_permissions = required_permissions

    def __call__(
        self,
        token: Annotated[str, Depends(oauth2_bearer)],
        db_session: Annotated[Session, Depends(get_db_session)],
    ) -> Union[UserModel, None]:
        user = get_current_user(token, db_session)
        if user.role.name == "Administrador" and user.is_staff:
            return user

        for perm in user.role.permissions:
            if (
                perm.module == self.required_permissions.module
                and perm.model == self.required_permissions.model
                and perm.action == self.required_permissions.action
            ):
                return user

        return None
