from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class {{ model_name }}Create(BaseModel):
    """Input schema for creating a {{ model_name.lower() }}."""
{%- for field in fields if field.name not in ['id', 'created_at', 'updated_at'] %}

    {{ field.name }}: {{ field.pydantic_type }}{% if field.nullable %} = None{% endif %}
{%- endfor %}

class {{ model_name }}Update(BaseModel):
    """Input schema for updating a {{ model_name.lower() }}."""
{%- for field in fields if field.name not in ['id', 'created_at', 'updated_at'] %}

    {{ field.name }}: Optional[{{ field.pydantic_type }}] = None
{%- endfor %}