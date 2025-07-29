"""
Management commands that require project settings.
These commands should be run through manage.py which sets up the Python path.
"""
import click
import asyncio
import shutil
from pathlib import Path
from tortoise import Tortoise
from aerich import Command
import sys
import subprocess
import jinja2
import uvicorn

from .settings import settings

# Base path for templates, can be overridden for testing
TEMPLATE_BASE = Path(__file__).parent / "scaffolds"

@click.group()
def cli():
    """Enlil management commands - run through manage.py"""
    pass

@cli.command()
def init_db():
    """Initialize the database and create first migration."""
    try:
        async def run_init():
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

                # Initialize aerich
                await command.init()

                # Create initial schema
                await command.init_db(safe=True)

                click.echo("Successfully initialized database.")
            finally:
                await Tortoise.close_connections()

        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_init())
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    except Exception as e:
        click.echo(f"Error initializing database: {str(e)}", err=True)
        raise

@cli.command()
@click.argument('app_name')
def startapp(app_name: str):
    """Create a new Enlil application."""
    click.echo(f"Creating new app: {app_name}")

    # Create app directory structure
    app_dir = Path("src/apps") / app_name
    template_dir = TEMPLATE_BASE / "app"

    # Check if app already exists
    if app_dir.exists():
        click.echo(f"Error: App '{app_name}' already exists", err=True)
        sys.exit(1)

    # Create main app directory
    app_dir.mkdir(exist_ok=True, parents=True)

    # Create necessary subdirectories
    (app_dir / "views").mkdir(exist_ok=True)
    (app_dir / "serializers").mkdir(exist_ok=True)
    (app_dir / "services").mkdir(exist_ok=True)
    (app_dir / "tests").mkdir(exist_ok=True)

    # Copy template files
    shutil.copy(template_dir / "models.py", app_dir / "models.py")
    shutil.copy(template_dir / "utils.py", app_dir / "utils.py")
    shutil.copy(template_dir / "routers.py", app_dir / "routers.py")

    # Create services directory
    services_dir = app_dir / "services"
    services_dir.mkdir(exist_ok=True)
    shutil.copy(template_dir / "services/base.py", services_dir / "base.py")
    (services_dir / "__init__.py").touch()

    # Copy views
    shutil.copy(template_dir / "views/api.py", app_dir / "views/api.py")
    shutil.copy(template_dir / "views/ui.py", app_dir / "views/ui.py")

    # Copy serializers
    shutil.copy(template_dir / "serializers/input.py", app_dir / "serializers/input.py")
    shutil.copy(template_dir / "serializers/output.py", app_dir / "serializers/output.py")
    shutil.copy(template_dir / "serializers/data_objects.py", app_dir / "serializers/data_objects.py")

    # Create __init__.py files
    (app_dir / "__init__.py").touch()
    (app_dir / "views" / "__init__.py").touch()
    (app_dir / "serializers" / "__init__.py").touch()
    (app_dir / "services" / "__init__.py").touch()
    (app_dir / "tests" / "__init__.py").touch()

    # Create basic test files
    shutil.copy(template_dir / "tests/conftest.py", app_dir / "tests/conftest.py")
    (app_dir / "tests" / "test_api.py").touch()
    (app_dir / "tests" / "test_ui.py").touch()

    click.echo(f"Created app structure in {app_dir}")
    click.echo("\nNext steps:")
    click.echo("1. Add your models to models.py")
    click.echo("2. Create your views in views/api.py and views/ui.py")
    click.echo("3. Define your serializers in serializers/")
    click.echo("4. Add your business logic to services.py")
    click.echo("5. Write tests in tests/")
    click.echo("\nIMPORTANT: Add your models to DB_MODELS in src/config.py:")
    click.echo(f'''    DB_MODELS.append("apps.{app_name}.models")''')
    click.echo("\nAfter updating config.py, run:")
    click.echo("1. python manage.py makemigrations")
    click.echo("2. python manage.py migrate")

@cli.command()
@click.argument('model_name')
@click.option('--app', required=True, help='App name where the model exists')
def makecrud(model_name: str, app: str):
    """Generate CRUD code for an existing model.

    Example: enlil makecrud Post --app blog
    """
    click.echo(f"Generating CRUD code for {model_name} in {app} app")

    # Validate app exists
    app_dir = Path("src/apps") / app
    if not app_dir.exists():
        click.echo(f"Error: App '{app}' does not exist", err=True)
        sys.exit(1)

    # Import and validate model exists
    try:
        import importlib
        models_module = importlib.import_module(f"src.apps.{app}.models")
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
    append_with_imports_at_top(api_file, view_code)

    # Write serializers
    serializers_dir = app_dir / "serializers"
    serializers_dir.mkdir(exist_ok=True)

    # Handle input.py
    input_file = serializers_dir / "input.py"
    if not input_file.exists():
        with open(input_file, "w") as f:
            f.write("from pydantic import BaseModel, Field\nfrom typing import Optional\nfrom datetime import datetime\n\n")
    append_with_imports_at_top(input_file, input_code)

    # Handle output.py
    output_file = serializers_dir / "output.py"
    if not output_file.exists():
        with open(output_file, "w") as f:
            f.write("from datetime import datetime\nfrom typing import Optional\n\nfrom pydantic import BaseModel, ConfigDict\n\n")
    append_with_imports_at_top(output_file, output_code)

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
    if not factory_file.exists():
        with open(factory_file, "w") as f:
            f.write("import factory\n\n")
    append_with_imports_at_top(factory_file, factory_code)

    # Generate test code using the test template
    test_template = env.get_template('crud/test/template.py')
    test_code = test_template.render(model_name=model_name, fields=field_list, app_name=app)
    with open(test_file, "w") as f:
        f.write(test_code)

    # Fix imports and format files using ruff
    try:
        import subprocess

        for file_path in [api_file, input_file, output_file]:
            click.echo(f"\nProcessing {file_path.name}...")

            # Read initial content for comparison
            with open(file_path, 'r') as f:
                original_content = f.read()
                click.echo(f"Original file size: {len(original_content)} bytes")
                print('original_content \n', original_content)

                subprocess.run([
                    "ruff", "check",
                    "--fix",
                    "--select", "E,F,I,UP,RUF",
                    "--fix-only",
                    "--unsafe-fixes",
                    str(file_path)
                ], check=False)

                # Final formatting to organize and reflow
                subprocess.run(["ruff", "format", str(file_path)], check=True)

            # Read final content
            with open(file_path, 'r') as f:
                final_content = f.read()
                click.echo(f"Final file size: {len(final_content)} bytes")
                print('final_content \n', final_content)

            if final_content != original_content:
                click.echo("File was modified successfully")
            else:
                click.echo("Warning: File content remained unchanged")

    except subprocess.CalledProcessError as e:
        click.echo(f"Error: command failed: {str(e)}", err=True)
        if hasattr(e, 'output'):
            click.echo(f"Command output: {e.output}")
    except Exception as e:
        click.echo(f"Error processing files: {str(e)}", err=True)

    click.echo(f"\nGenerated CRUD code for {model_name}")
    click.echo("Next steps:")
    click.echo("1. Review the generated code")
    click.echo("2. Run tests to verify everything works")

@cli.command()
def makemigrations():
    """Generate new database migrations (automatically initializes if needed)."""
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

                click.echo("Initializing aerich command...")

                # Check if this is the first time BEFORE running any init commands
                models_migration_dir = settings.MIGRATIONS_DIR / "models"
                is_first_time = not models_migration_dir.exists() or not any(models_migration_dir.glob("*.py"))

                # Check if aerich is initialized
                try:
                    await command.init()
                    click.echo("Initialized aerich for the first time.")

                    # Initialize database schema (always run this)
                    try:
                        await command.init_db(safe=True)
                        click.echo("Initialized database schema.")
                    except Exception as db_error:
                        if not any(msg in str(db_error).lower() for msg in ["already exists", "already initialized"]):
                            raise db_error

                except Exception as init_error:
                    # If it's not an "already initialized" error, and not a FileExistsError, raise it
                    if "already initialized" not in str(init_error) and not isinstance(init_error, FileExistsError):
                        raise init_error
                    # If it's already initialized, we can proceed with migrations
                    click.echo("Aerich already initialized, proceeding with migrations.")

                # Only generate new migrations if NOT first time
                if not is_first_time:
                    click.echo("Checking for model changes to generate new migrations...")
                    try:
                        migration_name = await command.migrate()
                        if migration_name:
                            click.echo(f"Created migration: {migration_name}")
                        else:
                            click.echo("No changes detected - no migration created.")
                    except FileExistsError as fee:
                        # This should only happen if there's a genuine file conflict
                        click.echo(f"Error: Migration file conflict detected at: {str(fee)}")
                        click.echo("This usually means:")
                        click.echo("1. A migration was created but not applied")
                        click.echo("2. There might be a timestamp collision")
                        click.echo("\nTry these steps:")
                        click.echo("1. Run 'python manage.py migrate' to apply existing migrations")
                        click.echo("2. If that doesn't help, delete the conflicting file and try again")
                        sys.exit(1)
                    except OSError as ose:
                        # Handle other file-related errors
                        click.echo(f"File system error while creating migration: {str(ose)}")
                        click.echo("This might be due to:")
                        click.echo("1. Permissions issues in the migrations directory")
                        click.echo("2. Disk space issues")
                        click.echo("3. File system restrictions")
                        sys.exit(1)
                else:
                    click.echo("First time setup complete. Run 'python manage.py migrate' to apply migrations.")

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

    except Exception as e:
        click.echo(f"Error creating migration: {str(e)}", err=True)
        if hasattr(e, '__cause__') and e.__cause__:
            click.echo(f"Caused by: {str(e.__cause__)}", err=True)
        sys.exit(1)

@cli.command()
def migrate():
    """Apply database migrations."""
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

def append_with_imports_at_top(file_path: Path, new_content: str):
    """When appending new content, put its imports at the top of destination file."""
    # Split new content into imports and rest
    imports = []
    rest = []

    for line in new_content.split('\n'):
        if line.strip().startswith(('from ', 'import ')):
            imports.append(line)
        else:
            rest.append(line)

    # Read current content
    try:
        with open(file_path, 'r') as f:
            current = f.read()
    except FileNotFoundError:
        current = ""

    # Write back with new imports at top
    with open(file_path, 'w') as f:
        if imports:
            f.write('\n'.join(imports) + '\n\n')
        if current:
            f.write(current)
        if rest:
            f.write('\n'.join(rest) + '\n')
