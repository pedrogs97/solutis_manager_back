"""Base exceptions"""

import logging
import traceback

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

    if error_status_code == 500:
        last_traceback = traceback.extract_tb(exc.__traceback__)[-1]
        file_name = last_traceback.filename
        line_number = last_traceback.lineno
        function_name = last_traceback.name

        extra = {}
        if request.method == "GET":
            extra["query_params"] = request.query_params
        elif request.method == "POST":
            extra["body"] = await request.json()
        extra["file"] = file_name
        extra["line"] = line_number
        extra["function"] = function_name
        message_error = f"Status {error_status_code}: {error_detail} - view: {request.url} - file: {file_name} - line: {line_number} - function: {function_name}"
        logger.error(
            msg=message_error,
            extra=extra,
        )
    else:
        logger.warning(
            "Status %s: %s - view: %s", error_status_code, error_detail, request.url
        )
    return JSONResponse(content=error_detail, status_code=error_status_code)
