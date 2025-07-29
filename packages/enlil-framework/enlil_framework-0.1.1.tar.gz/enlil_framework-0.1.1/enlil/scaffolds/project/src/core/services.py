"""
Base service classes for {{ project_name }}.

This module provides base service classes and utilities. You can:

1. Use enlil's built-in services:
   from enlil.core.services import BaseService

2. Create your own base service classes
3. Extend enlil's services with project-specific functionality
"""
from typing import TypeVar, Generic, Type
from tortoise import Model

ModelType = TypeVar("ModelType", bound=Model)

class BaseService(Generic[ModelType]):
    """Base service class for common CRUD operations.

    You can extend this or use enlil.core.services.BaseService directly.
    """

    def __init__(self, model_cls: Type[ModelType]):
        """Initialize the service with a model class."""
        self.model_cls = model_cls

    async def get_by_id(self, id: int) -> ModelType:
        """Get a model instance by ID."""
        return await self.model_cls.get(id=id)

    async def list_all(self) -> list[ModelType]:
        """List all instances."""
        return await self.model_cls.all()

    async def create(self, **kwargs) -> ModelType:
        """Create a new instance."""
        return await self.model_cls.create(**kwargs)

    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        """Update an instance."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await instance.save()
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete an instance."""
        await instance.delete()