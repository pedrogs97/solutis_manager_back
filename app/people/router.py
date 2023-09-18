"""People routes"""
from fastapi import APIRouter

people_router = APIRouter(prefix="/people", tags=["people"])
