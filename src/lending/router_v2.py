"""Lending router v2"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from src.lending.controllers.lending import LendingController

lending_router_v2 = APIRouter(prefix="/lendings", tags=["Lending V2"])


@lending_router_v2.post("/")
async def post_create_lending_flow_route(
    controller: LendingController = Depends(),
):
    """
    Creates a lending, uploads attachments, and generates a contract in a single flow.
    """
    result = await controller.create_lending_flow()

    return JSONResponse(
        content=result,
        status_code=status.HTTP_201_CREATED,
    )
