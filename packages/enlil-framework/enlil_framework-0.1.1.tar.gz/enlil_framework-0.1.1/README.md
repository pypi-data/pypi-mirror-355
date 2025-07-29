# Enlil

[![GitHub stars](https://img.shields.io/github/stars/entGriff/enlil?style=flat-square)](https://github.com/entGriff/enlil/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/entGriff/enlil?style=flat-square)](https://github.com/entGriff/enlil/issues)
[![GitHub forks](https://img.shields.io/github/forks/entGriff/enlil?style=flat-square)](https://github.com/entGriff/enlil/network)
[![PyPI version](https://img.shields.io/pypi/v/enlil-framework?style=flat-square)](https://pypi.org/project/enlil-framework/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)


A real frame built on the shoulders of FastAPI framework.
Enlil brings back the beauty of structured, modular design - old-school clarity fused with modern performance.

It's made for developers who value well-framed projects: organized apps, reusable services, sharp boundaries, and clean extensibility - all powered by FastAPI and Tortoise ORM.

## Features

- FastAPI-compatible
- Modular app structure
- Built-in ORM with Tortoise
- Jinja2 templating
- Dependency Injection
- CLI tools for scaffolding and CRUD

## Installation

Install Enlil from PyPI:

```bash
# Basic installation
pip install enlil-framework

# With development tools
pip install enlil-framework[dev]
```

## Quick Start

1. Create a new project:
```bash
enlil startproject myproject
cd myproject
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate     # Windows
```

3. Install additional dependencies if needed:

```bash
pip install -r requirements.txt
```

## CLI Commands

### Create a New App

```bash
enlil startapp <app_name>
```

This creates a new app with the following structure:

* `models.py`
* `views/api.py` and `views/ui.py`
* `serializers/input.py`, `output.py`, `data_objects.py`
* `services.py`, `utils.py`
* `routers.py`
* `tests/` directory

### Create Database Migrations

```bash
enlil makemigrations
```

Generates new database migrations based on model changes.

### Apply Database Migrations

```bash
enlil migrate
```

Applies pending database migrations to the database.

### Generate CRUD Endpoints

First, define your model in `models.py`, then generate CRUD endpoints:

```bash
enlil makecrud <ModelName> --app <app_name>
```

Example workflow:

1. Define a model in `apps/blog/models.py`:
```python
from tortoise.models import Model
from tortoise import fields

class Post(Model):
    title = fields.CharField(max_length=255)
    content = fields.TextField()
    is_published = fields.BooleanField(default=False)
```

2. Generate CRUD endpoints:
```bash
enlil makecrud Post --app blog
```

### Run Development Server

```bash
enlil runserver
```

Options:

* `--host`: Host to bind to (default: `127.0.0.1`)
* `--port`: Port to bind to (default: `8000`)

## Database Management

### After Model Changes

```bash
enlil makemigrations
enlil migrate
```

### Example Workflow

1. Create a model:
```python
class Post(models.Model):
    title = fields.CharField(max_length=255)
    content = fields.TextField()
    is_published = fields.BooleanField(default=False)
```

2. Generate and apply migrations:
```bash
enlil makemigrations
enlil migrate
```

3. Generate CRUD endpoints:
```bash
enlil makecrud Post --app blog
```

## Testing

Run all tests:

```bash
pytest
```

Run specific test:

```bash
pytest src/<app_name>/tests/test_api.py -v
```

## Project Structure

After creating a project with `enlil startproject myproject` and adding an app with `enlil startapp myapp`, your project structure will look like this:

```
myproject/
├── manage.py                   # Command-line utility for administrative tasks.
├── db.sqlite3                  # SQLite database file
├── pytest.ini                  # Pytest configuration
├── migrations/                 # Database migration files
│   └── models/
│       └── 0_20250606004453_init.py
├── src/                        # Source code directory
│   ├── __init__.py
│   ├── config.py               # Project configuration and settings
│   ├── conftest.py             # Pytest configuration for src/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/                   # Core framework components
│   │   ├── __init__.py
│   │   ├── containers.py       # Dependency injection containers
│   │   ├── database.py         # Database connection and setup
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   ├── exceptions.py       # Custom exception handlers
│   │   ├── models.py           # Base model classes
│   │   ├── services.py         # Base service classes
│   │   └── validators.py       # Data validation utilities
│   ├── apps/                   # Application modules
│   │   ├── __init__.py
│   │   └── myapp/              # Your application (created with startapp)
│   │       ├── __init__.py
│   │       ├── models.py       # App-specific models
│   │       ├── routers.py      # URL routing configuration
│   │       ├── utils.py        # App-specific utilities
│   │       ├── views/          # View controllers
│   │       │   ├── __init__.py
│   │       │   ├── api.py      # API endpoints
│   │       │   └── ui.py       # UI/template views
│   │       ├── serializers/    # Data serialization
│   │       │   ├── __init__.py
│   │       │   ├── input.py    # Input validation schemas
│   │       │   ├── output.py   # Output serialization schemas
│   │       │   └── data_objects.py # Data transfer objects
│   │       ├── services/       # Business logic
│   │       │   ├── __init__.py
│   │       │   └── base.py     # Base service classes
│   │       └── tests/          # App-specific tests
│   │           ├── __init__.py
│   │           ├── conftest.py # Test configuration
│   │           ├── test_api.py # API endpoint tests
│   │           └── test_ui.py  # UI view tests
│   └── templates/              # Jinja2 templates
│       ├── base.html           # Base template
│       └── index.html          # Home page template
```

## Environment Variables

Create a `.env` file in the project root:

```
DEBUG=true
DATABASE_URL=sqlite://db.sqlite3
SECRET_KEY=your-secret-key
TEMPLATE_DIR=templates
```

## Development Flow

1. Install enlil-framework: `pip install enlil-framework`
2. Create a project using `enlil startproject`
3. Create an app using `enlil startapp`
4. Define models in `models.py`
5. Generate and apply migrations: `enlil makemigrations` then `enlil migrate`
6. Generate CRUD endpoints: `enlil makecrud ModelName --app appname`
7. Write views in `views/api.py` and `views/ui.py`
8. Shape data in `serializers/`
9. Add logic in `services.py`
10. Write tests in `tests/`
11. Start the server with `enlil runserver`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the terms of the MIT license.
