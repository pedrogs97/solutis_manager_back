"""Datasync routes"""

import json
from typing import Union

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from src.auth.models import UserModel
from src.backends import PermissionChecker
from src.config import NOT_ALLOWED
from src.datasync.scheduler import SchedulerService

datasync_router = APIRouter(prefix="/fetch-totvs", tags=["Fetch"])


@datasync_router.post("/")
async def force_fetch_totvs(
    background_tasks: BackgroundTasks,
    request: Request,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "logs", "model": "log", "action": "view"})
    ),
):
    """Fetch data from TOTVS"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    scheduler = SchedulerService(force=True)
    background_tasks.add_task(scheduler.force_fetch)
    logger.info("recived from ip: {}", request.client.host)
    return Response(content=json.dumps({"message": "Sent fetch data"}))
