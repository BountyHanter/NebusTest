from fastapi import FastAPI

from logger.logging_config import setup_logging
from routers import organizations_router

app = FastAPI()

setup_logging(True)

app.include_router(organizations_router, prefix="/api", tags=["Organizations"])
