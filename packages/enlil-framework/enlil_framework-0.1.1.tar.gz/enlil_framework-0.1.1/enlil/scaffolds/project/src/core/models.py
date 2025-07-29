"""
Base models for {{ project_name }}.

This module extends the base models from enlil.core.models and adds project-specific
base classes and mixins. You can:

1. Import and use enlil's base models directly:
   from enlil.core.models import BaseModel

2. Extend enlil's base models with project-specific fields:
   from enlil.core.models import BaseModel as EnlilBaseModel

   class BaseModel(EnlilBaseModel):
       project_field = fields.CharField(max_length=100)

       class Meta:
           abstract = True

3. Create your own base models and mixins here
"""
from tortoise import fields, models

class BaseModel(models.Model):
    """Base model with common fields."""
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True