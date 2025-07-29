from tortoise import fields
from src.core.models import BaseModel

# Add your models here
class ExampleModel(BaseModel):
    """Example model with some basic fields."""
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

    class Meta:
        table = "example_models"