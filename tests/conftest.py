"""Pytest configuration and fixtures for Qlik Sense API tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

from src.api.main import app
from src.api.core.config import settings


@pytest.fixture
def client():
    """Test client fixture for FastAPI application.

    Returns:
        TestClient: Configured test client for making HTTP requests.
    """
    return TestClient(app)


@pytest.fixture
def mock_app_id():
    """Mock app ID for testing.

    Returns:
        str: Sample Qlik Sense application ID.
    """
    return "5a730580-3c25-4805-a2ef-dd4a71a91cda"


@pytest.fixture
def mock_app_name():
    """Mock app name for testing.

    Returns:
        str: Sample application name.
    """
    return "akfa-employees"


@pytest.fixture
def sample_pagination():
    """Sample pagination parameters.

    Returns:
        dict: Pagination parameters with page and page_size.
    """
    return {"page": 1, "page_size": 10}


@pytest.fixture
def sample_table_name():
    """Sample table name for testing.

    Returns:
        str: Sample table name from Qlik Sense app.
    """
    return "Employees"


@pytest.fixture
def mock_qlik_engine():
    """Mock Qlik Engine API client.

    Returns:
        Mock: Mocked Qlik Engine API client with common methods.
    """
    mock_engine = Mock()
    mock_engine.connect = Mock()
    mock_engine.disconnect = Mock()
    mock_engine.open_doc = Mock(return_value={
        "qReturn": {"qHandle": 1, "qType": "Doc"}
    })
    mock_engine.create_session_object = Mock(return_value={
        "qReturn": {"qHandle": 2}
    })
    mock_engine.get_layout = Mock(return_value={
        "qLayout": {
            "qHyperCube": {
                "qDataPages": [{
                    "qMatrix": [
                        [{"qText": "John Doe"}, {"qText": "Sales"}],
                        [{"qText": "Jane Smith"}, {"qText": "Engineering"}]
                    ]
                }],
                "qSize": {"qcy": 2}
            }
        }
    })
    return mock_engine


@pytest.fixture
def mock_app_repository():
    """Mock application repository.

    Returns:
        Mock: Mocked app repository with common methods.
    """
    mock_repo = Mock()
    mock_repo.list_all_apps = AsyncMock(return_value=[
        {
            "app_id": "5a730580-3c25-4805-a2ef-dd4a71a91cda",
            "app_name": "akfa-employees",
            "display_name": "AKFA Employees"
        }
    ])
    mock_repo.get_app_id_by_name = AsyncMock(
        return_value="5a730580-3c25-4805-a2ef-dd4a71a91cda"
    )
    mock_repo.get_app_by_id = AsyncMock(return_value={
        "app_id": "5a730580-3c25-4805-a2ef-dd4a71a91cda",
        "app_name": "AKFA Employees",
        "published": True
    })
    return mock_repo


@pytest.fixture
def mock_data_repository():
    """Mock data repository.

    Returns:
        Mock: Mocked data repository with common methods.
    """
    mock_repo = Mock()
    mock_repo.get_table_data = AsyncMock(return_value={
        "columns": ["Name", "Department"],
        "rows": [
            ["John Doe", "Sales"],
            ["Jane Smith", "Engineering"]
        ],
        "total_rows": 2
    })
    mock_repo.get_fields = AsyncMock(return_value=[
        {"name": "Name", "type": "string"},
        {"name": "Department", "type": "string"}
    ])
    return mock_repo


@pytest.fixture
def sample_filter_params():
    """Sample filter parameters for testing.

    Returns:
        dict: Filter parameters with field and value.
    """
    return {
        "field": "Department",
        "value": "Sales"
    }


@pytest.fixture
def sample_sort_params():
    """Sample sort parameters for testing.

    Returns:
        dict: Sort parameters with field and direction.
    """
    return {
        "field": "Name",
        "direction": "asc"
    }


@pytest.fixture
def mock_settings():
    """Mock application settings.

    Returns:
        Mock: Mocked settings object.
    """
    mock_config = Mock()
    mock_config.QLIK_SERVER_URL = "https://qlik.example.com"
    mock_config.QLIK_USER_DIRECTORY = "TEST"
    mock_config.QLIK_USER_ID = "testuser"
    mock_config.QLIK_CLIENT_CERT_PATH = "/path/to/cert.pem"
    mock_config.QLIK_CLIENT_KEY_PATH = "/path/to/key.pem"
    mock_config.QLIK_CA_CERT_PATH = "/path/to/ca.pem"
    mock_config.HOST = "0.0.0.0"
    mock_config.PORT = 8000
    mock_config.DEBUG = True
    mock_config.LOG_LEVEL = "INFO"
    return mock_config


@pytest.fixture
def sample_hypercube_request():
    """Sample hypercube request data.

    Returns:
        dict: Hypercube request with dimensions and measures.
    """
    return {
        "dimensions": ["Department", "Position"],
        "measures": ["Count([EmployeeID])", "Avg([Salary])"],
        "filters": [],
        "max_rows": 100
    }


@pytest.fixture
def sample_hypercube_response():
    """Sample hypercube response data.

    Returns:
        dict: Hypercube response with data matrix.
    """
    return {
        "dimensions": ["Department", "Position"],
        "measures": ["Count", "AvgSalary"],
        "data": [
            {"Department": "Sales", "Position": "Manager", "Count": 5, "AvgSalary": 75000},
            {"Department": "Sales", "Position": "Associate", "Count": 10, "AvgSalary": 50000},
            {"Department": "Engineering", "Position": "Senior", "Count": 8, "AvgSalary": 95000}
        ],
        "total_rows": 3
    }
