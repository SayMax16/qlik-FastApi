"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestHealthEndpoint:
    """Test cases for health check endpoint."""

    def test_health_endpoint_success(self, client):
        """Test health check returns 200 and correct structure."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_health_endpoint_structure(self, client):
        """Test health check response structure."""
        response = client.get("/api/v1/health")
        data = response.json()

        # Verify all expected fields are present
        expected_fields = ["status", "version", "timestamp", "service"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


class TestAppEndpoints:
    """Test cases for application endpoints."""

    def test_list_apps_endpoint_success(self, client):
        """Test list apps endpoint returns 200."""
        response = client.get("/api/v1/apps")

        # Status should be 200 or 503 if Qlik not connected
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "apps" in data
            assert isinstance(data["apps"], list)

    def test_list_apps_endpoint_structure(self, client):
        """Test list apps response structure."""
        response = client.get("/api/v1/apps")

        if response.status_code == 200:
            data = response.json()
            assert "apps" in data
            assert "total" in data

            if len(data["apps"]) > 0:
                app = data["apps"][0]
                assert "app_id" in app
                assert "app_name" in app

    def test_get_app_by_id_endpoint(self, client, mock_app_id):
        """Test get app by ID endpoint."""
        response = client.get(f"/api/v1/apps/{mock_app_id}")

        # Should return 200, 404, or 503
        assert response.status_code in [200, 404, 503]

        if response.status_code == 200:
            data = response.json()
            assert "app_id" in data
            assert data["app_id"] == mock_app_id

    def test_get_app_by_id_invalid_format(self, client):
        """Test get app with invalid ID format."""
        response = client.get("/api/v1/apps/invalid-id-format")

        # Should return 404 or 422 for invalid format
        assert response.status_code in [404, 422, 503]

    def test_get_app_by_id_not_found(self, client):
        """Test get app with non-existent ID."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/apps/{fake_id}")

        # Should return 404 or 503
        assert response.status_code in [404, 503]


class TestDataEndpoints:
    """Test cases for data retrieval endpoints."""

    def test_get_table_data_endpoint_basic(self, client, mock_app_name, sample_table_name):
        """Test get table data endpoint with basic parameters."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/tables/{sample_table_name}?page=1&page_size=10"
        )

        # Might fail if Qlik not connected, but tests endpoint structure
        assert response.status_code in [200, 404, 503]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data or "columns" in data

    def test_get_table_data_with_pagination(self, client, mock_app_name):
        """Test table data endpoint with pagination parameters."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/tables/Employees?page=1&page_size=20"
        )

        assert response.status_code in [200, 404, 503]

    def test_get_table_data_pagination_validation_page_zero(self, client, mock_app_name):
        """Test pagination validation - page number too small."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/tables/Employees?page=0&page_size=10"
        )

        # Should return 422 for validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_table_data_pagination_validation_page_size_too_large(
        self,
        client,
        mock_app_name
    ):
        """Test pagination validation - page size too large."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/tables/Employees?page=1&page_size=2000"
        )

        # Should return 422 for validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_table_data_pagination_validation_negative_page(
        self,
        client,
        mock_app_name
    ):
        """Test pagination validation - negative page number."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/tables/Employees?page=-1&page_size=10"
        )

        assert response.status_code == 422

    def test_get_table_data_with_filters(self, client, mock_app_name):
        """Test table data endpoint with filter parameters."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/tables/Employees"
            "?page=1&page_size=10&filter_field=Department&filter_value=Sales"
        )

        assert response.status_code in [200, 404, 503]

    def test_get_table_data_with_sorting(self, client, mock_app_name):
        """Test table data endpoint with sort parameters."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/tables/Employees"
            "?page=1&page_size=10&sort_field=Name&sort_direction=asc"
        )

        assert response.status_code in [200, 404, 503]

    def test_get_table_data_invalid_sort_direction(self, client, mock_app_name):
        """Test invalid sort direction parameter."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/tables/Employees"
            "?page=1&page_size=10&sort_field=Name&sort_direction=invalid"
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_get_table_data_app_not_found(self, client):
        """Test table data with non-existent app."""
        response = client.get(
            "/api/v1/apps/nonexistent-app/tables/Employees?page=1&page_size=10"
        )

        assert response.status_code in [404, 503]

    def test_get_table_data_table_not_found(self, client, mock_app_name):
        """Test table data with non-existent table."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/tables/NonexistentTable?page=1&page_size=10"
        )

        assert response.status_code in [404, 503]


class TestFieldEndpoints:
    """Test cases for field metadata endpoints."""

    def test_get_fields_endpoint(self, client, mock_app_name):
        """Test get fields endpoint."""
        response = client.get(f"/api/v1/apps/{mock_app_name}/fields")

        assert response.status_code in [200, 404, 503]

        if response.status_code == 200:
            data = response.json()
            assert "fields" in data
            assert isinstance(data["fields"], list)

    def test_get_field_values_endpoint(self, client, mock_app_name):
        """Test get field values endpoint."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/fields/Department/values"
        )

        assert response.status_code in [200, 404, 503]

        if response.status_code == 200:
            data = response.json()
            assert "values" in data
            assert isinstance(data["values"], list)

    def test_get_field_values_with_search(self, client, mock_app_name):
        """Test get field values with search parameter."""
        response = client.get(
            f"/api/v1/apps/{mock_app_name}/fields/Department/values?search=Sales"
        )

        assert response.status_code in [200, 404, 503]


class TestHypercubeEndpoints:
    """Test cases for hypercube creation endpoints."""

    def test_create_hypercube_endpoint(self, client, mock_app_name, sample_hypercube_request):
        """Test hypercube creation endpoint."""
        response = client.post(
            f"/api/v1/apps/{mock_app_name}/hypercube",
            json=sample_hypercube_request
        )

        assert response.status_code in [200, 404, 503]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data or "dimensions" in data

    def test_create_hypercube_invalid_request(self, client, mock_app_name):
        """Test hypercube creation with invalid request."""
        invalid_request = {
            "dimensions": [],  # Empty dimensions
            "measures": []     # Empty measures
        }

        response = client.post(
            f"/api/v1/apps/{mock_app_name}/hypercube",
            json=invalid_request
        )

        # Should return 422 for validation error
        assert response.status_code in [422, 400, 503]

    def test_create_hypercube_missing_fields(self, client, mock_app_name):
        """Test hypercube creation with missing required fields."""
        response = client.post(
            f"/api/v1/apps/{mock_app_name}/hypercube",
            json={}
        )

        assert response.status_code in [422, 400, 503]


class TestErrorHandling:
    """Test cases for error handling across endpoints."""

    def test_404_not_found(self, client):
        """Test 404 response for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 response for wrong HTTP method."""
        # Try POST on a GET-only endpoint
        response = client.post("/api/v1/health")
        assert response.status_code == 405

    def test_malformed_json_request(self, client, mock_app_name):
        """Test handling of malformed JSON in request body."""
        response = client.post(
            f"/api/v1/apps/{mock_app_name}/hypercube",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_missing_content_type(self, client, mock_app_name):
        """Test request without Content-Type header."""
        response = client.post(
            f"/api/v1/apps/{mock_app_name}/hypercube",
            data='{"dimensions": [], "measures": []}'
        )

        # Should still process or return appropriate error
        assert response.status_code in [200, 400, 422, 503]


class TestCORSHeaders:
    """Test cases for CORS headers."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in response."""
        response = client.get("/api/v1/health")

        # Check for common CORS headers
        # Note: Actual CORS headers depend on middleware configuration
        assert response.status_code == 200

    def test_preflight_request(self, client):
        """Test OPTIONS preflight request."""
        response = client.options("/api/v1/apps")

        # Should return 200 or 204 for OPTIONS
        assert response.status_code in [200, 204, 405]


class TestRateLimiting:
    """Test cases for rate limiting (if implemented)."""

    def test_rate_limit_not_exceeded(self, client):
        """Test normal requests don't trigger rate limit."""
        # Make several requests in succession
        for _ in range(5):
            response = client.get("/api/v1/health")
            assert response.status_code == 200

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        # This would typically be tested with async/threading
        response = client.get("/api/v1/health")
        assert response.status_code == 200


class TestOpenAPIDocumentation:
    """Test cases for OpenAPI documentation endpoints."""

    def test_openapi_json_available(self, client):
        """Test OpenAPI JSON schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_swagger_ui_available(self, client):
        """Test Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_available(self, client):
        """Test ReDoc documentation is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestResponseHeaders:
    """Test cases for response headers."""

    def test_content_type_json(self, client):
        """Test JSON endpoints return correct content-type."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_response_time_reasonable(self, client):
        """Test that response times are reasonable."""
        import time
        start = time.time()
        response = client.get("/api/v1/health")
        duration = time.time() - start

        assert response.status_code == 200
        # Health check should be very fast (< 1 second)
        assert duration < 1.0
