import factory
from factory.declarations import LazyFunction
from src.apps.{{ app_name }}.models import {{ model_name }}


class {{ model_name }}Factory(factory.Factory):
    class Meta:
        model = {{ model_name }}
        abstract = False

    {% for field in fields %}
    {% if field.name not in ['id', 'created_at', 'updated_at'] %}
    {{ field.name }} = factory.Faker('{{ field.faker_type }}')
    {% endif %}
    {% endfor %}

    @classmethod
    async def create(cls, **kwargs):
        """Create and save a new instance."""
        obj = cls.build(**kwargs)
        await obj.save()
        return obj

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to prevent synchronous creation."""
        raise NotImplementedError("Use create() instead")