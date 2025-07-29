from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.get("/")
async def index():
    """API root endpoint."""
    return {"status": "ok"}