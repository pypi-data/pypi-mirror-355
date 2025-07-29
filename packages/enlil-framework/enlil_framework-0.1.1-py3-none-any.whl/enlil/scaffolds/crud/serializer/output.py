from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class {{ model_name }}Response(BaseModel):
    """Output schema for {{ model_name.lower() }} data."""
    id: int
    created_at: datetime
    updated_at: datetime
{%- for field in fields if field.name not in ['id', 'created_at', 'updated_at'] %}

    {{ field.name }}: {% if field.type == 'CharField' or field.type == 'TextField' %}str{% elif field.type == 'IntField' %}int{% elif field.type == 'FloatField' %}float{% elif field.type == 'BooleanField' %}bool{% elif field.type == 'DateTimeField' %}datetime{% else %}str{% endif %}{% if field.nullable %} | None = None{% endif %}
{%- endfor %}

    model_config = ConfigDict(from_attributes=True)  # Enables ORM mode in Pydantic v2