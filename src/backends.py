"""Base backends"""

import asyncio
import logging
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated, Dict, List, Tuple, Union

import jinja2
import jwt
from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.auth.models import PermissionModel, TokenModel, UserModel
from src.auth.schemas import PermissionSchema
from src.config import (
    ACCESS_TOKEN_EXPIRE_HOURS,
    ALGORITHM,
    APP_URL,
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

logger = logging.getLogger(__name__)


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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

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
        db_session.close()
        raise get_user_exception() from exc


def token_is_valid(token: Union[TokenModel, dict]) -> bool:
    """Verifies token validity"""
    if token and isinstance(token, TokenModel):
        return token.expires_in > datetime.utcnow()

    if isinstance(token, dict) and token and "exp" in token:
        return (
            token["exp"] > datetime.utcnow().timestamp() and token["type"] == "access"
        )
    return False


def refresh_token_has_expired(token_str: str) -> bool:
    """Verifies refresh token validity"""
    try:
        token_decoded = jwt.decode(token_str, SECRET_KEY, algorithms=ALGORITHM)
        if "exp" not in token_decoded:
            return True
    except ExpiredSignatureError:
        return True
    return (
        token_decoded["exp"] < int(datetime.utcnow().timestamp())
        and token_decoded["type"] == "refresh"
    )


class PermissionChecker:
    """Dependence class for check permissions"""

    def __init__(
        self, required_permissions: Union[PermissionSchema, List[PermissionSchema]]
    ) -> None:
        self.required_permissions = required_permissions

    def check_perm(
        self, perm_to_check: PermissionSchema, user_perm: PermissionModel
    ) -> bool:
        """Check if user has permission"""
        return (
            perm_to_check["module"] == user_perm.module
            and perm_to_check["model"] == user_perm.model
            and perm_to_check["action"] == user_perm.action
        )

    def has_permissions(self, user: UserModel) -> bool:
        """Check if user has permission"""

        if user.group.name == "MASTER" or user.is_staff:
            return True

        if isinstance(self.required_permissions, list):
            for perm in self.required_permissions:
                for perm_user in user.group.permissions:
                    if self.check_perm(perm, perm_user):
                        return True
            return False

        for perm in user.group.permissions:
            if self.check_perm(self.required_permissions, perm):
                return True

        return False

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

            if not self.has_permissions(user):
                return None

            return user
        except jwt.ExpiredSignatureError:
            logger.warning("Invalid token")
            return None


# pylint: disable=too-few-public-methods
class Email365Client:
    """Office 365 email client com suporte a filas"""

    def __init__(
        self, mail_to: str, mail_subject: str, type_message: str, extra: Dict
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

        return template.render(
            username=self.__extra["username"],
            new_password=self.__extra["new_password"],
            full_name=self.__extra["full_name"],
        )

    def __prepare_new_user_password(self) -> str:
        """Build new user password email"""
        if "username" not in self.__extra:
            raise ValueError("Username not found to send new user email")
        if "password" not in self.__extra:
            raise ValueError("New password not found to send new user email")

        template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
        template_env = jinja2.Environment(loader=template_loader)
        template_file = "new_user_password.html"
        template = template_env.get_template(template_file)

        return template.render(
            username=self.__extra["username"],
            password=self.__extra["password"],
            full_name=self.__extra["full_name"],
        )

    def __prepare_notify_maintenance(self) -> str:
        """Build notify maintenance email"""
        if "id" not in self.__extra:
            raise ValueError("Id not found to notify maintenance email")
        if "full_name" not in self.__extra:
            raise ValueError("Employee name not found to send notify maintenance email")
        if "asset_type" not in self.__extra:
            raise ValueError("Asset type not found to send notify maintenance email")
        if "type" not in self.__extra:
            raise ValueError("Type not found to send notify maintenance email")

        template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
        template_env = jinja2.Environment(loader=template_loader)
        template_file = "notify_maintenance.html"
        template = template_env.get_template(template_file)

        return template.render(
            id=self.__extra["id"],
            full_name=self.__extra["full_name"],
            type=self.__extra["type"],
        )

    def __prepare_notify_inventory(self) -> str:
        """Build notify inventory email"""
        if "full_name" not in self.__extra:
            raise ValueError("full_name not found to notify inventory email")

        template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
        template_env = jinja2.Environment(loader=template_loader)
        template_file = "notify_inventory_link_email.html"
        template = template_env.get_template(template_file)

        return template.render(
            full_name=self.__extra["full_name"],
            inventory_link=f"{APP_URL}/inventory-access",
        )

    def __prepare_message(self) -> None:
        """Build email"""
        output_text = ""
        if self.__type == "new_password":
            output_text = self.__prepare_new_password()
        elif self.__type == "new_user":
            output_text = self.__prepare_new_user_password()
        elif self.__type == "notify_maintenance":
            output_text = self.__prepare_notify_maintenance()
        elif self.__type == "notify_inventory":
            output_text = self.__prepare_notify_inventory()

        self.__message.attach(MIMEText(output_text, "html"))

    def send_message(self, fake: bool = False) -> Tuple[bool, str]:
        """Try send message"""
        self.__prepare_message()
        try:
            with smtplib.SMTP(
                "smtp.office365.com", 587, local_hostname="solutis.com.br"
            ) as server:
                server.starttls()
                server.login(EMAIL_SOLUTIS_365, EMAIL_PASSWORD_SOLUTIS_365)
                if fake:
                    return True, self.__mail_to
                server.sendmail(
                    EMAIL_SOLUTIS_365, self.__mail_to, self.__message.as_string()
                )
            return True, self.__mail_to
        except smtplib.SMTPAuthenticationError:
            return False, self.__mail_to
        except smtplib.SMTPRecipientsRefused:
            return False, self.__mail_to


class EmailQueue:
    """Fila de envio de e-mails"""

    def __init__(self, max_workers: int = 5):
        self.queue = asyncio.Queue()
        self.max_workers = max_workers

    async def worker(self):
        """Worker que processa a fila de e-mails"""
        while True:
            email_task: Tuple[Email365Client, bool] = await self.queue.get()
            if email_task is None:
                break

            email_client, fake = email_task
            success, mail_to = email_client.send_message(fake=fake)
            if success:
                logger.info("Success sending email to %s", mail_to)
            else:
                logger.warning("Error sending email to %s", mail_to)

            self.queue.task_done()

    async def add_email_task(self, email_client: Email365Client, fake: bool = False):
        """Adiciona uma tarefa de envio de e-mail à fila"""
        await self.queue.put((email_client, fake))

    async def run(self):
        """Inicia os workers e processa a fila"""
        workers = [asyncio.create_task(self.worker()) for _ in range(self.max_workers)]
        await self.queue.join()

        for _ in range(self.max_workers):
            await self.queue.put(None)
        await asyncio.gather(*workers)
