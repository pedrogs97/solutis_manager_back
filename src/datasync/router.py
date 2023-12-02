"""Datasync routes"""
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Request, Response

from src.datasync.scheduler import SchedulerService

datasync_router = APIRouter(prefix="/fetch-totvs", tags=["Fetch"])

logger = logging.getLogger(__name__)


@datasync_router.post("/")
async def force_fetch_totvs(background_tasks: BackgroundTasks, request: Request):
    """Fetch data from TOTVS"""
    scheduler = SchedulerService(force=True)
    background_tasks.add_task(scheduler.force_fetch)
    logger.info("recived from ip: %s", request.client.host)
    return Response(content=json.dumps({"message": "Sent fetch data"}))
