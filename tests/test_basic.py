"""Basic tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint returns 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert "qlik_connection" in data


def test_list_apps_endpoint():
    """Test list apps endpoint."""
    response = client.get("/api/v1/apps")
    assert response.status_code in [200, 500, 503]  # May fail if Qlik not connected
    if response.status_code == 200:
        data = response.json()
        assert "apps" in data


def test_openapi_docs():
    """Test OpenAPI documentation is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


def test_pagination_validation():
    """Test pagination parameter validation."""
    # Invalid page (0)
    response = client.get("/api/v1/apps/test-app/tables/test?page=0")
    assert response.status_code == 422

    # Invalid page_size (too large)
    response = client.get("/api/v1/apps/test-app/tables/test?page_size=2000")
    assert response.status_code == 422

    # Negative page
    response = client.get("/api/v1/apps/test-app/tables/test?page=-1")
    assert response.status_code == 422


def test_sort_order_validation():
    """Test sort order validation."""
    # Invalid sort order
    response = client.get("/api/v1/apps/test-app/tables/test?sort_order=invalid")
    assert response.status_code == 422

    # Valid sort orders
    response = client.get("/api/v1/apps/test-app/tables/test?sort_order=asc")
    assert response.status_code in [200, 404, 503]

    response = client.get("/api/v1/apps/test-app/tables/test?sort_order=desc")
    assert response.status_code in [200, 404, 503]


def test_cors_headers():
    """Test CORS headers are present."""
    response = client.options("/api/v1/health")
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
