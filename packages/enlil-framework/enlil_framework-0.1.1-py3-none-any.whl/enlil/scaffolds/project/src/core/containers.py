"""
Dependency injection containers for {{ project_name }}.

This module sets up dependency injection using dependency-injector.
You can:

1. Use enlil's built-in containers:
   from enlil.core.containers import Container as EnlilContainer

2. Create your own containers and providers
3. Override enlil's container configuration
"""
from dependency_injector import containers, providers
from config import DEBUG, DATABASE_URL, SECRET_KEY

class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""

    # Configuration
    config = providers.Configuration(default={
        "debug": DEBUG,
        "database_url": DATABASE_URL,
        "secret_key": SECRET_KEY,
    })

    # Add your service providers here
    # Example:
    # user_service = providers.Factory(UserService)
    # auth_service = providers.Singleton(AuthService, secret_key=config.secret_key)