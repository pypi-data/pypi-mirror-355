"""
{{ project_name }} - Main Application Entry Point
"""
from fastapi import FastAPI
from tortoise import Tortoise
from src.config import TORTOISE_ORM
from src.core.database import init_db

def create_app(tortoise_config=None):
    """Create and configure the FastAPI application.

    Args:
        tortoise_config: Optional Tortoise ORM config. If not provided, uses default from config.py
    """
    app = FastAPI(title="{{ project_name }}")

    # Use provided config or fall back to default
    config = tortoise_config or TORTOISE_ORM

    @app.on_event("startup")
    async def init_orm():
        # Initialize Tortoise ORM
        await Tortoise.init(config=config)
        await Tortoise.generate_schemas()

        # Initialize database
        init_db()

    @app.on_event("shutdown")
    async def close_orm():
        await Tortoise.close_connections()

    @app.get("/")
    async def root():
        return {"message": "Welcome to {{ project_name }}"}

    # Include routers here as you create apps
    # Example:
    # from apps.blog.routers import router as blog_router
    # app.include_router(blog_router, tags=["blog"])

    return app

# Create the application instance
app = create_app()
