"""Base exceptions"""

import logging

from fastapi import status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.requests import Request

logger = logging.getLogger(__name__)


def get_user_exception() -> HTTPException:
    """Returns user exception"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return credentials_exception


def token_exception() -> HTTPException:
    """Returns credentials exception"""
    token_exception_response = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuário ou senha incorreto",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return token_exception_response


async def default_response_exception(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Returns default response exception"""
    error_detail = exc.detail if hasattr(exc, "detail") else "Undefined"
    error_status_code = exc.status_code if hasattr(exc, "status_code") else 500
    logger.warning(
        "Error %s: %s - view: %s", error_status_code, error_detail, request.url
    )
    return JSONResponse(content=error_detail, status_code=error_status_code)
