import pytest
from fastapi.testclient import TestClient
from src.apps.{{ app_name }}.models import {{ model_name }}
from src.apps.{{ app_name }}.serializers.input import {{ model_name }}Create, {{ model_name }}Update
from src.apps.{{ app_name }}.tests.factories import {{ model_name }}Factory

@pytest.mark.asyncio
async def test_create_{{ model_name.lower() }}(client: TestClient):
    """Test creating a new {{ model_name.lower() }}."""
    data = {
        {% for field in fields %}
        {% if field.name not in ['id', 'created_at', 'updated_at'] %}
        "{{ field.name }}": {% if field.type == 'CharField' or field.type == 'TextField' %}"test_{{ field.name }}"{% elif field.type == 'IntField' %}42{% elif field.type == 'FloatField' %}42.5{% elif field.type == 'BooleanField' %}True{% elif field.type == 'DateTimeField' %}"2024-01-01T00:00:00"{% else %}"test_{{ field.name }}"{% endif %},
        {% endif %}
        {% endfor %}
    }
    response = client.post("/api/{{ model_name.lower() }}s", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["id"] is not None
    {% for field in fields %}
    {% if field.name not in ['id', 'created_at', 'updated_at'] %}
    assert result["{{ field.name }}"] == data["{{ field.name }}"]
    {% endif %}
    {% endfor %}

@pytest.mark.asyncio
async def test_get_{{ model_name.lower() }}(client: TestClient):
    """Test getting a {{ model_name.lower() }} by ID."""
    obj = await {{ model_name }}Factory.create()
    response = client.get(f"/api/{{ model_name.lower() }}s/{obj.id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == obj.id
    {% for field in fields %}
    {% if field.name not in ['id', 'created_at', 'updated_at'] %}
    assert result["{{ field.name }}"] == obj.{{ field.name }}
    {% endif %}
    {% endfor %}

@pytest.mark.asyncio
async def test_get_{{ model_name.lower() }}_not_found(client: TestClient):
    """Test getting a non-existent {{ model_name.lower() }}."""
    response = client.get("/api/{{ model_name.lower() }}s/99999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_list_{{ model_name.lower() }}s(client: TestClient):
    """Test listing all {{ model_name.lower() }}s."""
    {{ model_name.lower() }}s = []
    for _ in range(3):
        {{ model_name.lower() }}s.append(await {{ model_name }}Factory.create())
    response = client.get("/api/{{ model_name.lower() }}s")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 3

@pytest.mark.asyncio
async def test_update_{{ model_name.lower() }}(client: TestClient):
    """Test updating a {{ model_name.lower() }}."""
    obj = await {{ model_name }}Factory.create()
    data = {
        {% for field in fields %}
        {% if field.name not in ['id', 'created_at', 'updated_at'] %}
        "{{ field.name }}": {% if field.type == 'CharField' or field.type == 'TextField' %}"updated_{{ field.name }}"{% elif field.type == 'IntField' %}99{% elif field.type == 'FloatField' %}99.9{% elif field.type == 'BooleanField' %}False{% elif field.type == 'DateTimeField' %}"2024-02-01T00:00:00"{% else %}"updated_{{ field.name }}"{% endif %},
        {% endif %}
        {% endfor %}
    }
    response = client.put(f"/api/{{ model_name.lower() }}s/{obj.id}", json=data)
    assert response.status_code == 200
    result = response.json()
    {% for field in fields %}
    {% if field.name not in ['id', 'created_at', 'updated_at'] %}
    assert result["{{ field.name }}"] == data["{{ field.name }}"]
    {% endif %}
    {% endfor %}

@pytest.mark.asyncio
async def test_update_{{ model_name.lower() }}_not_found(client: TestClient):
    """Test updating a non-existent {{ model_name.lower() }}."""
    data = {
        {% for field in fields %}
        {% if field.name not in ['id', 'created_at', 'updated_at'] %}
        "{{ field.name }}": {% if field.type == 'CharField' or field.type == 'TextField' %}"updated_{{ field.name }}"{% elif field.type == 'IntField' %}99{% elif field.type == 'FloatField' %}99.9{% elif field.type == 'BooleanField' %}False{% elif field.type == 'DateTimeField' %}"2024-02-01T00:00:00"{% else %}"updated_{{ field.name }}"{% endif %},
        {% endif %}
        {% endfor %}
    }
    response = client.put("/api/{{ model_name.lower() }}s/99999", json=data)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_{{ model_name.lower() }}(client: TestClient):
    """Test deleting a {{ model_name.lower() }}."""
    obj = await {{ model_name }}Factory.create()
    response = client.delete(f"/api/{{ model_name.lower() }}s/{obj.id}")
    assert response.status_code == 200

    # Verify deletion
    response = client.get(f"/api/{{ model_name.lower() }}s/{obj.id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_{{ model_name.lower() }}_not_found(client: TestClient):
    """Test deleting a non-existent {{ model_name.lower() }}."""
    response = client.delete("/api/{{ model_name.lower() }}s/99999")
    assert response.status_code == 404