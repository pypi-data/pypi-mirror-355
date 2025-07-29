from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel

from src.core.services import BaseService
from src.apps.{{ app_name }}.models import {{ model_name }}
from src.apps.{{ app_name }}.serializers.input import {{ model_name }}Create, {{ model_name }}Update
from src.apps.{{ app_name }}.serializers.output import {{ model_name }}Response

InputType = TypeVar("InputType", bound=BaseModel)
UpdateType = TypeVar("UpdateType", bound=BaseModel)
OutputType = TypeVar("OutputType", bound=BaseModel)

class BaseCrudService(Generic[InputType, UpdateType, OutputType]):
    """Base CRUD service class with common functionality."""

    async def create(self, data: InputType) -> OutputType:
        """Create a new item."""
        raise NotImplementedError

    async def get(self, id: int) -> OutputType:
        """Get a single item by ID."""
        raise NotImplementedError

    async def list(self) -> List[OutputType]:
        """List all items."""
        raise NotImplementedError

    async def update(self, id: int, data: Optional[UpdateType] = None) -> OutputType:
        """Update an item."""
        raise NotImplementedError

    async def delete(self, id: int) -> None:
        """Delete an item."""
        raise NotImplementedError


class {{ model_name }}Service(BaseCrudService[{{ model_name }}Create, {{ model_name }}Update, {{ model_name }}Response]):
    """Service for handling {{ model_name.lower() }} operations."""

    def _to_response(self, obj: {{ model_name }}) -> {{ model_name }}Response:
        """Convert Tortoise ORM model to Pydantic response."""
        return {{ model_name }}Response(
            id=obj.id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,{% for field in fields %}
            {{ field.name }}=obj.{{ field.name }},
{% endfor %}        )

    async def create(self, data: {{ model_name }}Create) -> {{ model_name }}Response:
        """Create a new {{ model_name.lower() }}."""
        obj = await {{ model_name }}.create(**data.model_dump())
        return self._to_response(obj)

    async def get(self, id: int) -> {{ model_name }}Response:
        """Get a {{ model_name.lower() }} by ID."""
        obj = await {{ model_name }}.get(id=id)
        return self._to_response(obj)

    async def list(self) -> List[{{ model_name }}Response]:
        """List all {{ model_name.lower() }}s."""
        objs = await {{ model_name }}.all()
        return [self._to_response(obj) for obj in objs]

    async def update(self, id: int, data: Optional[{{ model_name }}Update] = None) -> {{ model_name }}Response:
        """Update a {{ model_name.lower() }}."""
        obj = await {{ model_name }}.get(id=id)
        if data:
            update_data = data.model_dump(exclude_unset=True)
            await obj.update_from_dict(update_data).save()
        return self._to_response(obj)

    async def delete(self, id: int) -> None:
        """Delete a {{ model_name.lower() }}."""
        await {{ model_name }}.filter(id=id).delete()