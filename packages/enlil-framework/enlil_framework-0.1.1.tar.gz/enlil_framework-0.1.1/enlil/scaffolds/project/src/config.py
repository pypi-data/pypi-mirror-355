"""
Settings for {{ project_name }} project.
"""
from pathlib import Path
import secrets

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secrets.token_urlsafe(32)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database settings
DATABASE_URL = "sqlite://./db.sqlite3"

# Update Tortoise ORM config with project-specific models
TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "aerich.models",
                # Add your models here:
                # "src.apps.myapp.models"
            ],
            "default_connection": "default",
        },
    },
}

# Migrations directory
MIGRATIONS_DIR = BASE_DIR / "migrations"

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

# Templates
TEMPLATE_DIRS = [
    BASE_DIR / "src" / "templates",
]

# Security
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CORS_ORIGINS = []

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}