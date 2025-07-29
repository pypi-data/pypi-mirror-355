import click
import os
import shutil
from pathlib import Path
import jinja2
import re
import subprocess
import sqlite3
import sys

from .settings import settings, ENVIRONMENT_VARIABLE

# Base path for templates, can be overridden for testing
TEMPLATE_BASE = Path(__file__).parent / "scaffolds"

# Flag to skip formatting in tests
SKIP_FORMAT = False

def validate_project_name(project_name: str) -> bool:
    """Validate that a project name is a valid Python package name."""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", project_name):
        return False
    return True

def create_jinja_env(template_dir: Path) -> jinja2.Environment:
    """Create a Jinja2 environment with proper template loading."""
    # Create a file system loader that looks in both the project root and templates dir
    template_paths = [
        str(template_dir),  # For most files
        str(template_dir / "src" / "templates"),  # For HTML templates
    ]

    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_paths),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )

def initialize_database(project_dir: Path, project_name: str) -> None:
    """Initialize the SQLite database and run initial migrations."""
    # Create database file
    db_file = project_dir / "db.sqlite3"
    sqlite3.connect(db_file).close()

    # Update config.py to point to the correct database file
    config_file = project_dir / "src" / "config.py"
    if config_file.exists():
        config_content = config_file.read_text()
        config_content = config_content.replace(
            'DATABASE_URL = "sqlite://db.sqlite3"',
            'DATABASE_URL = "sqlite://./db.sqlite3"'
        )
        config_file.write_text(config_content)

@click.group()
def cli():
    """Enlil - A Python web framework built on FastAPI"""
    pass

@cli.command()
@click.argument('project_name')
@click.option('--no-git', is_flag=True, help='Skip git initialization')
def startproject(project_name: str, no_git: bool):
    """Create a new Enlil project.

    Example: enlil startproject mysite
    """
    click.echo(f"Creating new project: {project_name}")

    # Validate project name
    if not validate_project_name(project_name):
        click.echo(f"Error: '{project_name}' is not a valid Python package name", err=True)
        click.echo("Project names must start with a letter and contain only letters, numbers, and underscores", err=True)
        sys.exit(1)

    # Check if directory already exists
    if Path(project_name).exists():
        click.echo(f"Error: Directory '{project_name}' already exists", err=True)
        sys.exit(1)

    # Create project from template
    template_dir = TEMPLATE_BASE / "project"
    if not template_dir.exists():
        click.echo(f"Error: Project template not found at {template_dir}", err=True)
        sys.exit(1)

    # Setup Jinja environment
    env = create_jinja_env(template_dir)

    # Create project directory
    project_dir = Path(project_name)
    project_dir.mkdir()

    # Copy and render all files from template
    for template_path in template_dir.rglob("*"):
        if template_path.is_file():
            # Get relative path from template root
            relative_path = template_path.relative_to(template_dir)

            # Create target path
            target_path = project_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # If it's a template file, render it
            if template_path.suffix in [".py", ".html", ".md", ".toml"]:
                try:
                    template = env.get_template(str(relative_path))
                    rendered = template.render(project_name=project_name)
                    target_path.write_text(rendered)
                except jinja2.TemplateNotFound as e:
                    click.echo(f"Warning: Template not found: {e.name}", err=True)
                    # Copy file as-is if template not found
                    shutil.copy2(template_path, target_path)
            else:
                # Otherwise just copy it
                shutil.copy2(template_path, target_path)

    # Create empty apps directory with __init__.py
    apps_dir = project_dir / "src" / "apps"
    apps_dir.mkdir(parents=True, exist_ok=True)
    apps_init = apps_dir / "__init__.py"
    apps_init.write_text(f'''"""
Application modules for {project_name}.

This directory contains all the application modules. Each app should be a Python package
with its own models, views, serializers, and services.

To create a new app:
    python manage.py startapp myapp
"""
''')

    # Initialize database
    initialize_database(project_dir, project_name)

    # Initialize git repository
    if not no_git:
        try:
            subprocess.run(["git", "init", str(project_dir)], check=True)
            click.echo("Initialized git repository")
        except subprocess.CalledProcessError:
            click.echo("Warning: Failed to initialize git repository", err=True)
        except FileNotFoundError:
            click.echo("Warning: Git not found, skipping repository initialization", err=True)

    click.echo(f"\nCreated project {project_name}")
    click.echo("\nNext steps:")
    click.echo(f"1. cd {project_name}")
    click.echo("2. python manage.py startapp myapp")
    click.echo("3. python manage.py runserver")

@cli.command()
@click.argument('model_name')
@click.option('--app', required=True, help='App name where the model exists')
def makecrud(model_name: str, app: str):
    """Generate CRUD code for an existing model.

    Example: enlil makecrud Post --app blog
    """
    from config import MIGRATIONS_DIR, TORTOISE_ORM

    click.echo(f"Generating CRUD code for {model_name} in {app} app")

    # Validate app exists
    app_dir = Path("src/apps") / app
    if not app_dir.exists():
        click.echo(f"Error: App '{app}' does not exist", err=True)
        sys.exit(1)

    # Import and validate model exists
    try:
        import importlib
        models_module = importlib.import_module(f"apps.{app}.models")
        model_class = getattr(models_module, model_name)
    except ImportError:
        click.echo(f"Error: Could not import models from app '{app}'", err=True)
        sys.exit(1)
    except AttributeError:
        click.echo(f"Error: Model '{model_name}' not found in app '{app}'", err=True)
        sys.exit(1)

    # Get model description
    model_desc = model_class.describe(serializable=False)

    # Extract field information
    field_list = []
    for field in model_desc['data_fields']:
        if field['name'] not in ['id', 'created_at', 'updated_at']:
            field_list.append({
                'name': field['name'],
                'type': field['field_type'].__name__,
                'pydantic_type': field['python_type'].__name__,
                'faker_type': get_faker_type(field['python_type'].__name__),
                'nullable': field['nullable'],
                'unique': field['unique']
            })

    # Setup Jinja environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_BASE)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )

    # Generate serializers
    input_template = env.get_template('crud/serializer/input.py')
    input_code = input_template.render(model_name=model_name, fields=field_list)

    output_template = env.get_template('crud/serializer/output.py')
    output_code = output_template.render(model_name=model_name, fields=field_list)

    # Generate service
    service_template = env.get_template('crud/service/template.py')
    service_code = service_template.render(model_name=model_name, fields=field_list, app_name=app)

    # Create views directory and api.py if they don't exist
    views_dir = app_dir / "views"
    views_dir.mkdir(exist_ok=True)
    api_file = views_dir / "api.py"
    if not api_file.exists():
        api_file.write_text('from fastapi import APIRouter\n\nrouter = APIRouter(prefix="/api")\n\n@router.get("/")\nasync def index():\n    """API root endpoint."""\n    return {"status": "ok"}\n')

    # Generate view code and append to api.py
    view_template = env.get_template('crud/view/template.py')
    view_code = view_template.render(model_name=model_name, fields=field_list, app_name=app)
    with open(api_file, "a") as f:
        f.write("\n\n" + view_code)

    # Write serializers
    serializers_dir = app_dir / "serializers"
    serializers_dir.mkdir(exist_ok=True)
    with open(serializers_dir / "input.py", "w") as f:
        f.write(input_code)
    with open(serializers_dir / "output.py", "w") as f:
        f.write(output_code)

    # Create service file
    service_file = app_dir / "services" / f"{model_name.lower()}.py"
    service_file.parent.mkdir(exist_ok=True)
    with open(service_file, "w") as f:
        f.write(service_code)

    # Create __init__.py if it doesn't exist
    (app_dir / "services" / "__init__.py").touch()

    # Create test directory
    test_dir = app_dir / "tests"
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / f"test_{model_name.lower()}.py"

    # Generate factory code using the factory template
    factory_template = env.get_template('crud/factory/template.py')
    factory_code = factory_template.render(model_name=model_name, fields=field_list, app_name=app)
    factory_file = test_dir / "factories.py"
    with open(factory_file, "w" if not factory_file.exists() else "a") as f:
        if not factory_file.exists():
            f.write("import factory\n\n")
        f.write("\n\n" + factory_code)

    # Generate test code using the test template
    test_template = env.get_template('crud/test/template.py')
    test_code = test_template.render(model_name=model_name, fields=field_list, app_name=app)
    with open(test_file, "w") as f:
        f.write(test_code)

    # Run ruff on modified files
    if not SKIP_FORMAT:
        files_to_format = [
            api_file,
            app_dir / "services" / f"{model_name.lower()}.py",
            serializers_dir / "input.py",
            serializers_dir / "output.py",
            test_file,
            factory_file
        ]
        try:
            for file in files_to_format:
                subprocess.run(["ruff", "check", "--fix", "--select", "E,F,I,UP,RUF", "--fix-only", "--unsafe-fixes", str(file)], check=False)
                subprocess.run(["ruff", "format", str(file)], check=True)
            click.echo("Formatted generated files")
        except subprocess.CalledProcessError:
            click.echo("Warning: Failed to format some files", err=True)

    click.echo(f"\nGenerated CRUD code for {model_name}")
    click.echo("Next steps:")
    click.echo("1. Review the generated code")
    click.echo("2. Run tests to verify everything works")

@cli.command()
def makemigrations():
    """Generate new database migrations (automatically initializes if needed)."""
    # Set settings module path
    os.environ.setdefault(ENVIRONMENT_VARIABLE, "src.config")

    try:
        async def run_migrations():
            # Ensure migrations directory exists
            settings.MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

            # Initialize Tortoise first
            await Tortoise.init(config=settings.TORTOISE_ORM)

            try:
                # Initialize aerich command with explicit migrations location
                command = Command(
                    tortoise_config=settings.TORTOISE_ORM,
                    app="models",
                    location=str(settings.MIGRATIONS_DIR)
                )

                # Check if aerich needs initialization
                try:
                    await command.init()
                    click.echo("Initialized aerich for the first time.")
                except Exception as init_error:
                    # If already initialized, just continue
                    if "already initialized" not in str(init_error):
                        raise

                # Check if database needs initialization
                try:
                    await command.init_db(safe=True)
                except Exception as db_error:
                    # If already initialized, just continue
                    if "already exists" not in str(db_error):
                        raise

                # Generate migrations
                migration_name = await command.migrate()
                if migration_name:
                    click.echo(f"Created migration: {migration_name}")
                else:
                    click.echo("No changes detected - no migration created.")
            finally:
                await Tortoise.close_connections()

        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_migrations())
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    except FileExistsError:
        click.echo("Migration file already exists. Run 'enlil migrate' to apply it.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error creating migration: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def migrate():
    """Apply database migrations."""
    # Set settings module path
    os.environ.setdefault(ENVIRONMENT_VARIABLE, "src.config")

    try:
        async def run_upgrade():
            try:
                # Initialize aerich command first
                command = Command(
                    tortoise_config=settings.TORTOISE_ORM,
                    app="models",
                    location=str(settings.MIGRATIONS_DIR)
                )

                # Initialize Tortoise through Command to ensure migrations are properly set up
                await command.init()

                # Apply migrations
                await command.upgrade()
                click.echo("Successfully applied migrations.")
            finally:
                # Make sure we close all connections
                try:
                    await Tortoise.close_connections()
                except Exception:
                    pass

        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_upgrade())
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    except Exception as e:
        click.echo(f"Error applying migrations: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def init_db():
    """Initialize the database and create first migration."""
    # Set settings module path
    os.environ.setdefault(ENVIRONMENT_VARIABLE, "src.config")

    try:
        async def run_init():
            # Initialize aerich command
            command = Command(
                tortoise_config=settings.TORTOISE_ORM,
                app="models",
                location=str(settings.MIGRATIONS_DIR)
            )

            # Initialize the database
            await command.init()

            # Create initial schema
            await command.init_db()

        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_init())
        finally:
            loop.close()

        click.echo("Successfully initialized database.")

    except Exception as e:
        click.echo(f"Error initializing database: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
def runserver(host: str, port: int):
    """Run the development server."""
    uvicorn.run("src.main:app", host=host, port=port, reload=True)

def get_faker_type(python_type: str) -> str:
    """Convert Python type to Faker type."""
    type_map = {
        'str': 'word',
        'int': 'random_int',
        'float': 'pyfloat',
        'bool': 'boolean',
        'datetime': 'date_time',
        'date': 'date',
        'time': 'time',
        'email': 'email',
        'url': 'url',
        'uuid': 'uuid4',
        'text': 'paragraph',  # For longer text fields
        'slug': 'slug',
        'ip': 'ipv4',
        'json': 'json',
        'list': 'pylist',
        'dict': 'pydict',
    }
    return type_map.get(python_type, 'word')

if __name__ == '__main__':
    cli()
