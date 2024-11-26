from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.backends import get_db_session
from src.config import SECRET_KEY
from src.people.models import EmployeeModel

security = HTTPBearer()


def verify_token(
    db_session: Annotated[Session, Depends(get_db_session)],
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        if (
            not payload
            and not payload.get("registration")
            and not payload.get("birthday")
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        employee = (
            db_session.query(EmployeeModel)
            .filter(
                EmployeeModel.registration == payload["registration"],
                EmployeeModel.birthday == payload["birthday"],
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
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")
