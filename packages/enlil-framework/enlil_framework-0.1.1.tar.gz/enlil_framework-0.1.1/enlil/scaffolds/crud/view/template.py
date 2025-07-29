from fastapi import APIRouter, Depends
from typing import List

from src.core.dependencies import model_resolver
from src.apps.{{ app_name }}.models import {{ model_name }}
from src.apps.{{ app_name }}.services.{{ model_name.lower() }} import {{ model_name }}Service
from src.apps.{{ app_name }}.serializers.input import {{ model_name }}Create, {{ model_name }}Update
from src.apps.{{ app_name }}.serializers.output import {{ model_name }}Response

@router.post("/{{ model_name.lower() }}s", response_model={{ model_name }}Response, tags=["{{ model_name.lower() }}s"])
async def create_{{ model_name.lower() }}(
    data: {{ model_name }}Create,
    service: {{ model_name }}Service = Depends()
) -> {{ model_name }}Response:
    """Create a new {{ model_name.lower() }}."""
    return await service.create(data)

@router.get("/{{ model_name.lower() }}s/{id}", response_model={{ model_name }}Response, tags=["{{ model_name.lower() }}s"])
async def get_{{ model_name.lower() }}(
    {{ model_name.lower() }}: {{ model_name }} = Depends(model_resolver({{ model_name }})),
    service: {{ model_name }}Service = Depends()
) -> {{ model_name }}Response:
    """Get a {{ model_name.lower() }} by ID."""
    return await service.get({{ model_name.lower() }}.id)

@router.get("/{{ model_name.lower() }}s", response_model=List[{{ model_name }}Response], tags=["{{ model_name.lower() }}s"])
async def list_{{ model_name.lower() }}s(
    service: {{ model_name }}Service = Depends()
) -> List[{{ model_name }}Response]:
    """List all {{ model_name.lower() }}s."""
    return await service.list()

@router.put("/{{ model_name.lower() }}s/{id}", response_model={{ model_name }}Response, tags=["{{ model_name.lower() }}s"])
async def update_{{ model_name.lower() }}(
    {{ model_name.lower() }}: {{ model_name }} = Depends(model_resolver({{ model_name }})),
    data: {{ model_name }}Update = None,
    service: {{ model_name }}Service = Depends()
) -> {{ model_name }}Response:
    """Update a {{ model_name.lower() }}."""
    return await service.update({{ model_name.lower() }}.id, data)

@router.delete("/{{ model_name.lower() }}s/{id}", tags=["{{ model_name.lower() }}s"])
async def delete_{{ model_name.lower() }}(
    {{ model_name.lower() }}: {{ model_name }} = Depends(model_resolver({{ model_name }})),
    service: {{ model_name }}Service = Depends()
) -> None:
    """Delete a {{ model_name.lower() }}."""
    await service.delete({{ model_name.lower() }}.id)