"""Base backends"""
import logging
import smtplib
import time
from datetime import datetime, timedelta
from typing import Annotated, Union

import jwt
from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
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
                    perm.module == self.required_permissions.module
                    and perm.model == self.required_permissions.model
                    and perm.action == self.required_permissions.action
                ):
                    return user
            return None
        except jwt.ExpiredSignatureError:
            logger.warning("Invalid token")
            return None


class Email365Client:
    """Office 365 email client"""

    conf = ConnectionConfig(
        MAIL_USERNAME=EMAIL_SOLUTIS_365,
        MAIL_PASSWORD=EMAIL_PASSWORD_SOLUTIS_365,
        MAIL_FROM=EMAIL_SOLUTIS_365,
        MAIL_PORT=587,
        MAIL_SERVER="smtp-mail.outlook.com",
        MAIL_FROM_NAME="Solutis Agile",
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )

    def __init__(self, mail_to: str, mail_subject: str, mail_body: str) -> None:
        self.__mail_to = mail_to
        self.__mail_subject = mail_subject
        self.__mail_body = mail_body
        self.message = MessageSchema(
            subject=self.__mail_subject,
            recipients=[self.__mail_to],
            body=self.__mail_body,
            subtype=MessageType.html,
        )
        logger.info(self.conf.model_dump())
        self.fm = FastMail(self.conf)

    async def send_message(self) -> bool:
        """Try send message"""
        logger.info("Sending message to %s", self.__mail_to)
        # try:
        #     await self.fm.send_message(self.message)
        #     return True
        # except ValueError:
        #     logger.error("Unable to sent message")
        #     return False

        sender = EMAIL_SOLUTIS_365

        message = f"""\
        Subject: Hi Mailtrap
        To: {self.__mail_to}
        From: {sender}

        This is a test e-mail message."""

        with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
            server.login(EMAIL_SOLUTIS_365, EMAIL_PASSWORD_SOLUTIS_365)
            server.sendmail(sender, self.__mail_to, message)
        return True

        # with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
        #     server.login("c6d190177572f4", "bff9f2516dd37c")
        #     server.sendmail(sender, self.__mail_to, message)
        # return True
