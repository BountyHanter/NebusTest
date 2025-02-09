from fastapi import APIRouter

from .organizations import router as organizations_router

router = APIRouter()

router.include_router(organizations_router, prefix="/organizations")