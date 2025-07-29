"""
Database initialization and utilities.
"""
from tortoise import Tortoise
from src.config import TORTOISE_ORM

async def init_db():
    """Initialize the database connection."""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()