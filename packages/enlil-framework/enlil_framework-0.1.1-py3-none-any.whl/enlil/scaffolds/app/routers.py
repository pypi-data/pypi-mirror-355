from fastapi import APIRouter
from .views import api, ui

router = APIRouter()

# Include API routes
router.include_router(api.router)

# Include UI routes
router.include_router(ui.router)