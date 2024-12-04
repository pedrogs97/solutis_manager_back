from datetime import datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.backends import get_db_session
from src.config import ACCESS_TOKEN_EXPIRE_HOURS, SECRET_KEY
from src.people.models import EmployeeModel

security = HTTPBearer()


def verify_token(
    db_session: Annotated[Session, Depends(get_db_session)],
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        registration = payload.get("registration")
        birthday = payload.get("birthday")
        expires_in = payload.get("expires_in")

        if not payload and not registration and not birthday and not expires_in:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        if datetime.now() > datetime.strptime(expires_in, "%Y-%m-%d %H:%M:%S"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Token expired"
            )

        employee = (
            db_session.query(EmployeeModel)
            .filter(
                EmployeeModel.registration == registration,
                EmployeeModel.birthday == birthday,
            )
            .first()
        )

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def generate_token(data: dict):
    access_expire_in = datetime.now() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {**data, "expires_in": access_expire_in.strftime("%Y-%m-%d %H:%M:%S")},
        SECRET_KEY,
        algorithm="HS256",
    )
