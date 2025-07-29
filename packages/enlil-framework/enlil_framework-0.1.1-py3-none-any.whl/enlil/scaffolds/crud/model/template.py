from tortoise import fields
from enlil.models import BaseModel

class {{ model_name }}(BaseModel):
    """{{ model_name }} model for storing {{ model_name.lower() }} data."""

    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    {% for field in fields %}
    {{ field.name }} = fields.{{ field.type }}Field({% if field.type == 'Char' %}max_length=255{% if field.nullable or field.unique %}, {% endif %}{% endif %}{% if field.nullable %}null=True{% if field.unique %}, {% endif %}{% endif %}{% if field.unique %}unique=True{% endif %})
    {% endfor %}

    class Meta:
        table = "{{ model_name.lower() }}s"
        table_description = "{{ model_name }} table for storing {{ model_name.lower() }} data"

    def __str__(self):
        return f"{{ model_name }}(id={self.id})"