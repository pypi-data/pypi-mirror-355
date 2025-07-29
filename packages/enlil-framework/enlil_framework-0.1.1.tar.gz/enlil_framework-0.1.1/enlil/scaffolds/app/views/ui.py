from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """UI root endpoint."""
    return """
    <html>
        <head><title>Welcome</title></head>
        <body>
            <h1>Welcome to your Enlil app!</h1>
        </body>
    </html>
    """