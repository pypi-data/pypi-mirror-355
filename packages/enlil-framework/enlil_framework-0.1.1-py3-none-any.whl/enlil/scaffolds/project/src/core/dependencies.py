from typing import Type, TypeVar, Optional
from fastapi import Depends, HTTPException, status
from tortoise.exceptions import DoesNotExist

ModelType = TypeVar("ModelType")

async def get_model_by_id(
    model_class: Type[ModelType],
    id: int,
    error_message: Optional[str] = None
) -> ModelType:
    """Generic dependency to get a model instance by ID.

    Args:
        model_class: The Tortoise ORM model class
        id: The ID to look up
        error_message: Optional custom error message

    Returns:
        The model instance if found

    Raises:
        HTTPException: If the model is not found
    """
    try:
        return await model_class.get(id=id)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message or f"{model_class.__name__} with id {id} not found"
        )

def model_resolver(
    model_class: Type[ModelType],
    error_message: Optional[str] = None
):
    """Create a FastAPI dependency for resolving a model by ID.

    Args:
        model_class: The Tortoise ORM model class
        error_message: Optional custom error message

    Returns:
        A FastAPI dependency function
    """
    async def _resolve_model(id: int) -> ModelType:
        return await get_model_by_id(model_class, id, error_message)
    return _resolve_model