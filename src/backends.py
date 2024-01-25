"""Base backends"""
import logging
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated, Union

import jinja2
import jwt
from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.auth.models import TokenModel, UserModel
from src.auth.schemas import PermissionSchema
from src.config import (
    ACCESS_TOKEN_EXPIRE_HOURS,
    ALGORITHM,
    EMAIL_PASSWORD_SOLUTIS_365,
    EMAIL_SOLUTIS_365,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    TEMPLATE_DIR,
)
from src.database import Session_db
from src.exceptions import get_user_exception, token_exception

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/")

logger = logging.Logger(__name__)


def get_db_session():
    """Return session"""
    return Session_db()


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


def get_user_from_refresh(
    refresh_token: str, db_session: Session
) -> Union[UserModel, None]:
    """Returns authenticated user if exists"""
    token_decoded = jwt.decode(refresh_token, SECRET_KEY, algorithms=ALGORITHM)
    user = (
        db_session.query(UserModel)
        .filter(
            UserModel.id == token_decoded["sub"],
        )
        .first()
    )
    return user


def logout_user(token: str, db_session: Session) -> None:
    """Logouts user"""
    try:
        token_decoded = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        user = get_current_user(token_decoded, db_session)
        old_token = (
            db_session.query(TokenModel).filter(TokenModel.user_id == user.id).first()
        )

        if not old_token:
            raise token_exception()

        db_session.delete(old_token)
        db_session.commit()
    except PyJWTError:
        logger.warning("Failed logout")


def get_user_token(user: UserModel, db_session: Session) -> dict:
    """Returns user token"""

    user.last_login_in = datetime.utcnow()
    db_session.add(user)
    db_session.commit()

    old_token = (
        db_session.query(TokenModel).filter(TokenModel.user_id == user.id).first()
    )

    if not user.group:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    permissions = [
        f"{perm.module}_{perm.model}_{perm.action}" for perm in user.group.permissions
    ]

    access_expire_in = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_expire_timestamp = int(time.mktime(access_expire_in.timetuple()))

    refresh_expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_expire_timestamp = time.mktime(refresh_expire.timetuple())
    if not token_is_valid(old_token):
        encode = {
            "iat": datetime.now().timestamp(),
            "exp": access_expire_timestamp,
            "sub": user.id,
            "type": "access",
        }

        token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

        refresh_encode = {
            "iat": datetime.now().timestamp(),
            "exp": refresh_expire_timestamp,
            "sub": user.id,
            "type": "refresh",
        }

        refresh_token = jwt.encode(refresh_encode, SECRET_KEY, algorithm=ALGORITHM)

        token_db = TokenModel(
            user=user,
            token=token,
            expires_in=access_expire_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expire,
        )

        if old_token:
            db_session.delete(old_token)
            db_session.commit()

        db_session.add(token_db)
        db_session.commit()

        return {
            "id": user.id,
            "group": user.group.name,
            "email": user.email,
            "full_name": user.employee.full_name if user.employee else "Usuário",
            "access_token": token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": access_expire_timestamp,
            "permissions": permissions,
        }

    return {
        "id": user.id,
        "group": user.group.name,
        "email": user.email,
        "full_name": user.employee.full_name if user.employee else "Usuário",
        "access_token": old_token.token,
        "refresh_token": old_token.refresh_token,
        "token_type": "Bearer",
        "expires_in": old_token.expires_in.timestamp(),
        "permissions": permissions,
    }


def get_current_user(token: dict, db_session: Session) -> UserModel:
    """Returns current user from token"""
    try:
        user_id: int = token.get("sub")
        if user_id is None:
            raise get_user_exception()

        user_db = db_session.query(UserModel).filter(UserModel.id == user_id).first()

        if not user_db:
            raise get_user_exception()

        return user_db
    except jwt.ExpiredSignatureError as exc:
        raise get_user_exception() from exc


def token_is_valid(token: Union[TokenModel, dict]) -> bool:
    """Verifies token validity"""
    if isinstance(token, TokenModel):
        if not token:
            return False
        return token.expires_in > datetime.utcnow()

    if isinstance(token, dict):
        if not token or "exp" not in token:
            return False
        return (
            token["exp"] > datetime.utcnow().timestamp() and token["type"] == "access"
        )


def refresh_token_has_expired(token_str: str) -> bool:
    """Verifies refresh token validity"""
    try:
        token_decoded = jwt.decode(token_str, SECRET_KEY, algorithms=ALGORITHM)
        if "exp" not in token_decoded:
            return False
    except ExpiredSignatureError:
        return False
    return (
        token_decoded["exp"] < int(datetime.utcnow().timestamp())
        and token_decoded["type"] == "refresh"
    )


class PermissionChecker:
    """Dependence class for check permissions"""

    def __init__(self, required_permissions: PermissionSchema) -> None:
        self.required_permissions = required_permissions

    def __call__(
        self,
        token: Annotated[str, Depends(oauth2_bearer)],
        db_session: Annotated[Session, Depends(get_db_session)],
    ) -> Union[UserModel, None]:
        try:
            token_decoded = jwt.decode(str(token), SECRET_KEY, algorithms=ALGORITHM)
            if not token_is_valid(token_decoded):
                return None
            user = get_current_user(token_decoded, db_session)

            if user.group.name == "Administrador" and user.is_staff:
                return user

            for perm in user.group.permissions:
                if (
                    perm.module == self.required_permissions["module"]
                    and perm.model == self.required_permissions["model"]
                    and perm.action == self.required_permissions["action"]
                ):
                    return user
            return None
        except jwt.ExpiredSignatureError:
            logger.warning("Invalid token")
            return None


class Email365Client:
    """Office 365 email client"""

    # https://realpython.com/python-send-email/

    def __init__(
        self, mail_to: str, mail_subject: str, type_message: str, extra: dict
    ) -> None:
        self.__extra = extra
        self.__type = type_message
        self.__mail_to = mail_to
        self.__message = MIMEMultipart("alternative")
        self.__message["Subject"] = mail_subject
        self.__message["From"] = EMAIL_SOLUTIS_365
        self.__message["To"] = mail_to

    def __prepare_new_password(self) -> str:
        """Build new password email"""
        if "username" not in self.__extra:
            raise ValueError("Username not found to send new password email")
        if "new_password" not in self.__extra:
            raise ValueError("New password not found to send new password email")

        template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
        template_env = jinja2.Environment(loader=template_loader)
        template_file = "reset_password.html"
        template = template_env.get_template(template_file)

        return template.render(username="teste", new_password="teste senha")

    def __prepare_message(self) -> None:
        """Build email"""
        output_text = ""
        if self.__type == "new_password":
            output_text = self.__prepare_new_password()

        self.__message.attach(MIMEText(output_text, "html"))

    def send_message(self, fake=False) -> bool:
        """Try send message"""
        self.__prepare_message()
        try:
            with smtplib.SMTP(
                "smtp.office365.com", 587, local_hostname="solutis.com.br"
            ) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(EMAIL_SOLUTIS_365, EMAIL_PASSWORD_SOLUTIS_365)
                if fake:
                    return True
                server.sendmail(
                    EMAIL_SOLUTIS_365, self.__mail_to, self.__message.as_string()
                )
            return True
        except smtplib.SMTPAuthenticationError:
            return False
        except smtplib.SMTPRecipientsRefused:
            return False
