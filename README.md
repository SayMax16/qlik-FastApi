# Qlik Sense REST API

A modern, high-performance REST API for retrieving data from Qlik Sense applications with built-in pagination, filtering, sorting, and comprehensive error handling.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Certificate Setup](#certificate-setup)
- [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Features

- **FastAPI Framework**: High-performance async Python web framework
- **Qlik Sense Integration**: Direct access to Qlik Sense Enterprise data
- **Pagination Support**: Efficient handling of large datasets
- **Field Filtering**: Filter data by any field with flexible operators
- **Sorting**: Multi-field sorting with ascending/descending support
- **Certificate Authentication**: Secure authentication using client certificates
- **Auto-generated Documentation**: Interactive Swagger UI and ReDoc
- **Type Safety**: Full type hints and validation with Pydantic
- **Error Handling**: Comprehensive error messages and logging
- **CORS Support**: Configurable CORS for cross-origin requests

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Applications                   │
│         (Web Apps, Mobile Apps, BI Tools)               │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ HTTP/REST
                  │
┌─────────────────▼───────────────────────────────────────┐
│              Qlik Sense REST API (FastAPI)              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  API Layer (Endpoints)                          │   │
│  │  - /health, /apps, /tables, /hypercube          │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  Service Layer                                   │   │
│  │  - AppService, DataService                      │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  Repository Layer                                │   │
│  │  - AppRepository, DataRepository                │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  Client Layer                                    │   │
│  │  - QlikEngineClient, QlikRepositoryClient       │   │
│  └──────────────────┬──────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ WebSocket (WSS:4747)
                     │ HTTPS (4242)
                     │
┌────────────────────▼────────────────────────────────────┐
│           Qlik Sense Enterprise Server                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Engine API (Data Extraction)                    │  │
│  │  - Hypercubes, Fields, Measures                  │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Repository API (Metadata)                       │  │
│  │  - Apps, Streams, Objects                        │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

- **API Layer**: HTTP request handling, validation, response formatting
- **Service Layer**: Business logic, orchestration, error handling
- **Repository Layer**: Data access patterns, caching, query building
- **Client Layer**: Low-level API communication, connection management

## Installation

### Prerequisites

- Python 3.9 or higher
- Qlik Sense Enterprise (February 2018+)
- Valid Qlik Sense client certificates
- Network access to Qlik Sense server (ports 4242, 4747)

### Using pip

```bash
# Clone the repository
git clone <repository-url>
cd qlik-sense-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd qlik-sense-api

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

## Configuration

### Environment Variables

Create a `.env` file in the project root directory:

```bash
# Qlik Sense Server Configuration
QLIK_SERVER_URL=https://qlik.your-company.com
QLIK_USER_DIRECTORY=YOUR_DOMAIN
QLIK_USER_ID=your-username

# Certificate Paths (absolute paths recommended)
QLIK_CLIENT_CERT_PATH=/path/to/certs/client.pem
QLIK_CLIENT_KEY_PATH=/path/to/certs/client_key.pem
QLIK_CA_CERT_PATH=/path/to/certs/root.pem

# Network Configuration
QLIK_REPOSITORY_PORT=4242  # Repository API port (default: 4242)
QLIK_ENGINE_PORT=4747      # Engine API WebSocket port (default: 4747)
QLIK_PROXY_PORT=4243       # Proxy port for authentication (default: 4243)

# SSL Configuration
QLIK_VERIFY_SSL=true       # Verify SSL certificates (default: true)

# API Server Configuration
HOST=0.0.0.0               # Server host (default: 0.0.0.0)
PORT=8000                  # Server port (default: 8000)
DEBUG=false                # Debug mode (default: false)
LOG_LEVEL=INFO             # Logging level (DEBUG, INFO, WARNING, ERROR)

# CORS Configuration
CORS_ORIGINS=*             # Allowed origins (* for all, or comma-separated list)
CORS_CREDENTIALS=true      # Allow credentials in CORS requests

# Performance Tuning
WORKERS=4                  # Number of worker processes (production)
TIMEOUT=30                 # Request timeout in seconds
MAX_PAGE_SIZE=1000         # Maximum allowed page size for pagination
```

### Configuration File Structure

```
qlik-sense-api/
├── .env                   # Environment variables (DO NOT commit)
├── .env.example           # Example environment file (commit this)
├── pyproject.toml         # Project dependencies
└── certs/                 # SSL certificates directory
    ├── client.pem         # Client certificate
    ├── client_key.pem     # Client private key
    └── root.pem           # CA root certificate
```

## Certificate Setup

### Obtaining Certificates from Qlik Sense

1. **Connect to Qlik Sense Server** (requires administrative access):

```bash
# Via RDP or SSH to Qlik Sense server
cd C:\ProgramData\Qlik\Sense\Repository\Exported Certificates\.Local Certificates
```

2. **Export Certificates** for your user:
   - Go to Qlik Management Console (QMC)
   - Navigate to: Certificates > Export certificates
   - Select your user directory and user ID
   - Download the certificate package

3. **Convert Certificates** to PEM format:

```bash
# Extract from ZIP
unzip client_certificates.zip

# If in PFX format, convert to PEM
openssl pkcs12 -in client.pfx -out client.pem -nokeys
openssl pkcs12 -in client.pfx -out client_key.pem -nocerts -nodes
openssl pkcs12 -in client.pfx -out root.pem -cacerts -nokeys
```

4. **Place Certificates** in `certs/` directory:

```bash
mkdir -p certs
mv client.pem certs/
mv client_key.pem certs/
mv root.pem certs/
chmod 600 certs/*  # Secure permissions
```

### Certificate Troubleshooting

**Issue**: "Certificate verification failed"
- Ensure certificates are in PEM format
- Check file permissions (should be readable)
- Verify certificate dates (not expired)

**Issue**: "Failed to authenticate"
- Verify QLIK_USER_DIRECTORY matches certificate
- Verify QLIK_USER_ID matches certificate
- Check certificate was exported for correct user

## Running the Server

### Development Mode

With auto-reload enabled for development:

```bash
# Using run.py
python run.py

# Using uvicorn directly
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

With multiple workers for production:

```bash
# Using uvicorn with multiple workers
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn with Uvicorn workers
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run with Docker
docker build -t qlik-sense-api .
docker run -p 8000:8000 --env-file .env -v $(pwd)/certs:/app/certs qlik-sense-api
```

## API Endpoints

### Health Check

#### GET /api/v1/health

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-27T12:00:00Z",
  "service": "Qlik Sense REST API"
}
```

### Application Management

#### GET /api/v1/apps

List all available Qlik Sense applications.

**Response:**
```json
{
  "apps": [
    {
      "app_id": "5a730580-3c25-4805-a2ef-dd4a71a91cda",
      "app_name": "akfa-employees",
      "display_name": "AKFA Employees",
      "published": true,
      "stream": "Everyone"
    }
  ],
  "total": 1
}
```

#### GET /api/v1/apps/{app_id}

Get details for a specific application.

**Parameters:**
- `app_id` (path): Application ID

**Response:**
```json
{
  "app_id": "5a730580-3c25-4805-a2ef-dd4a71a91cda",
  "app_name": "AKFA Employees",
  "description": "Employee data and analytics",
  "published": true,
  "tables": ["Employees", "Departments", "Salaries"]
}
```

### Data Retrieval

#### GET /api/v1/apps/{app_name}/tables/{table_name}

Retrieve data from a specific table with pagination, filtering, and sorting.

**Parameters:**
- `app_name` (path): Application name (e.g., "akfa-employees")
- `table_name` (path): Table name (e.g., "Employees")
- `page` (query): Page number (default: 1, min: 1)
- `page_size` (query): Items per page (default: 100, min: 1, max: 1000)
- `filter_field` (query, optional): Field to filter by
- `filter_value` (query, optional): Value to filter for
- `sort_field` (query, optional): Field to sort by
- `sort_direction` (query, optional): Sort direction ("asc" or "desc")

**Example Request:**
```bash
GET /api/v1/apps/akfa-employees/tables/Employees?page=1&page_size=10&filter_field=Department&filter_value=Sales&sort_field=Name&sort_direction=asc
```

**Response:**
```json
{
  "app_name": "akfa-employees",
  "table_name": "Employees",
  "columns": ["EmployeeID", "Name", "Department", "Salary"],
  "data": [
    {
      "EmployeeID": "E001",
      "Name": "John Doe",
      "Department": "Sales",
      "Salary": 65000
    },
    {
      "EmployeeID": "E002",
      "Name": "Jane Smith",
      "Department": "Sales",
      "Salary": 72000
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_rows": 45,
    "total_pages": 5
  }
}
```

#### GET /api/v1/apps/{app_name}/fields

Get list of all available fields in an application.

**Response:**
```json
{
  "app_name": "akfa-employees",
  "fields": [
    {
      "name": "EmployeeID",
      "type": "string",
      "cardinality": 1250
    },
    {
      "name": "Department",
      "type": "string",
      "cardinality": 12
    },
    {
      "name": "Salary",
      "type": "numeric",
      "min": 35000,
      "max": 150000
    }
  ]
}
```

#### GET /api/v1/apps/{app_name}/fields/{field_name}/values

Get unique values for a specific field.

**Parameters:**
- `search` (query, optional): Search string to filter values

**Response:**
```json
{
  "field_name": "Department",
  "values": [
    "Sales",
    "Engineering",
    "HR",
    "Finance",
    "Operations"
  ],
  "count": 5
}
```

### Hypercube Queries

#### POST /api/v1/apps/{app_name}/hypercube

Create and execute a custom hypercube query for advanced data analysis.

**Request Body:**
```json
{
  "dimensions": ["Department", "Position"],
  "measures": [
    "Count([EmployeeID])",
    "Avg([Salary])",
    "Sum([Salary])"
  ],
  "filters": [
    {
      "field": "Status",
      "value": "Active"
    }
  ],
  "max_rows": 100
}
```

**Response:**
```json
{
  "app_name": "akfa-employees",
  "dimensions": ["Department", "Position"],
  "measures": ["Employee Count", "Avg Salary", "Total Salary"],
  "data": [
    {
      "Department": "Sales",
      "Position": "Manager",
      "Employee Count": 5,
      "Avg Salary": 85000,
      "Total Salary": 425000
    },
    {
      "Department": "Sales",
      "Position": "Associate",
      "Employee Count": 40,
      "Avg Salary": 55000,
      "Total Salary": 2200000
    }
  ],
  "total_rows": 2
}
```

### Error Responses

All endpoints return consistent error responses:

**400 Bad Request:**
```json
{
  "error": "Bad Request",
  "message": "Invalid filter parameters",
  "details": "filter_field is required when filter_value is provided"
}
```

**404 Not Found:**
```json
{
  "error": "Not Found",
  "message": "Application 'unknown-app' not found"
}
```

**422 Validation Error:**
```json
{
  "error": "Validation Error",
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error"
    }
  ]
}
```

**503 Service Unavailable:**
```json
{
  "error": "Service Unavailable",
  "message": "Failed to connect to Qlik Sense server",
  "details": "Connection timeout after 30 seconds"
}
```

## Testing

### Running Tests

Run all tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

Run specific test file:
```bash
pytest tests/unit/test_services.py
```

Run specific test:
```bash
pytest tests/integration/test_endpoints.py::TestHealthEndpoint::test_health_endpoint_success
```

### Test Categories

**Unit Tests** (`tests/unit/`):
- Service layer logic
- Data validation
- Business rule enforcement
- Mock external dependencies

**Integration Tests** (`tests/integration/`):
- API endpoint behavior
- Request/response validation
- Error handling
- End-to-end workflows

### Test Coverage

Generate HTML coverage report:
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

Target coverage: 80%+ overall, 90%+ for critical paths

## Examples

### Example 1: Get All Employees

```bash
curl -X GET "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?page=1&page_size=100" \
  -H "Accept: application/json"
```

### Example 2: Filter Employees by Department

```bash
curl -X GET "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?page=1&page_size=50&filter_field=Department&filter_value=Engineering" \
  -H "Accept: application/json"
```

### Example 3: Sort and Paginate Results

```bash
curl -X GET "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?page=2&page_size=20&sort_field=Salary&sort_direction=desc" \
  -H "Accept: application/json"
```

### Example 4: Employee Count by Department

```bash
curl -X POST "http://localhost:8000/api/v1/apps/akfa-employees/hypercube" \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": ["Department"],
    "measures": ["Count([EmployeeID])"],
    "max_rows": 100
  }'
```

### Example 5: Salary Analysis by Department and Position

```bash
curl -X POST "http://localhost:8000/api/v1/apps/akfa-employees/hypercube" \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": ["Department", "Position"],
    "measures": [
      "Count([EmployeeID])",
      "Avg([Salary])",
      "Min([Salary])",
      "Max([Salary])"
    ],
    "filters": [
      {
        "field": "Status",
        "value": "Active"
      }
    ],
    "max_rows": 500
  }'
```

### Example 6: Get Available Fields

```bash
curl -X GET "http://localhost:8000/api/v1/apps/akfa-employees/fields" \
  -H "Accept: application/json"
```

### Example 7: Get Department Values

```bash
curl -X GET "http://localhost:8000/api/v1/apps/akfa-employees/fields/Department/values" \
  -H "Accept: application/json"
```

### Python Client Example

```python
import requests

class QlikSenseClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def get_employees(self, department=None, page=1, page_size=100):
        """Get employees with optional department filter."""
        params = {
            "page": page,
            "page_size": page_size
        }

        if department:
            params["filter_field"] = "Department"
            params["filter_value"] = department

        response = self.session.get(
            f"{self.base_url}/api/v1/apps/akfa-employees/tables/Employees",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_salary_analysis(self):
        """Get salary analysis by department."""
        payload = {
            "dimensions": ["Department"],
            "measures": [
                "Count([EmployeeID])",
                "Avg([Salary])",
                "Min([Salary])",
                "Max([Salary])"
            ]
        }

        response = self.session.post(
            f"{self.base_url}/api/v1/apps/akfa-employees/hypercube",
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage
client = QlikSenseClient()

# Get all employees in Sales
sales_employees = client.get_employees(department="Sales")
print(f"Found {sales_employees['pagination']['total_rows']} sales employees")

# Get salary analysis
salary_data = client.get_salary_analysis()
for row in salary_data['data']:
    print(f"{row['Department']}: {row['Employee Count']} employees, "
          f"Avg: ${row['Avg Salary']:,.2f}")
```

## Troubleshooting

### Common Issues

#### 1. Certificate Authentication Failures

**Symptom:** `503 Service Unavailable` - "Failed to authenticate with Qlik Sense"

**Solutions:**
- Verify certificate paths in `.env` are correct and absolute
- Check certificates are in PEM format (not PFX/P12)
- Ensure `QLIK_USER_DIRECTORY` and `QLIK_USER_ID` match certificate
- Verify certificates are not expired: `openssl x509 -in client.pem -noout -dates`
- Check file permissions: `chmod 600 certs/*`

#### 2. Connection Timeouts

**Symptom:** `503 Service Unavailable` - "Connection timeout"

**Solutions:**
- Verify Qlik Sense server URL is correct
- Check network connectivity: `ping qlik.your-company.com`
- Verify firewall allows ports 4242 and 4747
- Check if VPN connection is required
- Increase timeout in `.env`: `TIMEOUT=60`

#### 3. Application Not Found

**Symptom:** `404 Not Found` - "Application 'app-name' not found"

**Solutions:**
- List available apps: `GET /api/v1/apps`
- Verify app name spelling (case-sensitive)
- Check user has access to the app in Qlik Sense
- Verify app is published (if required)

#### 4. Table/Field Not Found

**Symptom:** `404 Not Found` - "Table 'table-name' not found"

**Solutions:**
- Get available fields: `GET /api/v1/apps/{app_name}/fields`
- Check table name spelling (case-sensitive)
- Verify table exists in Qlik Sense data model
- Check data load script has executed successfully

#### 5. Pagination Validation Errors

**Symptom:** `422 Validation Error` - "ensure this value is greater than 0"

**Solutions:**
- Ensure `page >= 1`
- Ensure `page_size >= 1` and `page_size <= MAX_PAGE_SIZE`
- Check query parameters are properly URL-encoded

#### 6. Slow Performance

**Symptoms:** Requests taking longer than expected

**Solutions:**
- Reduce `page_size` for large datasets
- Add filters to limit data volume
- Use specific field selections instead of `SELECT *`
- Check Qlik Sense server performance
- Enable caching for frequently accessed data
- Increase worker count in production

#### 7. SSL Certificate Verification

**Symptom:** SSL verification errors

**Solutions:**
- If using self-signed certificates, set `QLIK_VERIFY_SSL=false`
- For production, use properly signed certificates
- Add CA certificate to system trust store

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# In .env file
LOG_LEVEL=DEBUG
DEBUG=true
```

View detailed logs:
```bash
python run.py 2>&1 | tee debug.log
```

### Health Check Diagnostics

Check service health with detailed diagnostics:

```bash
curl http://localhost:8000/api/v1/health
```

Expected healthy response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-27T12:00:00Z",
  "service": "Qlik Sense REST API"
}
```

## Development

### Code Style

Format code with Black:
```bash
black src/ tests/
```

Lint code with Ruff:
```bash
ruff check src/ tests/
```

Type checking with mypy:
```bash
mypy src/
```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pre-commit install
```

### Project Structure

```
qlik-sense-api/
├── src/api/                # Application source code
│   ├── __init__.py
│   ├── main.py            # FastAPI application entry
│   ├── api/               # API routes
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── apps.py
│   │           ├── data.py
│   │           └── health.py
│   ├── core/              # Core configuration
│   │   ├── config.py      # Settings and configuration
│   │   ├── dependencies.py # Dependency injection
│   │   └── exceptions.py  # Custom exceptions
│   ├── schemas/           # Pydantic models
│   │   ├── app.py
│   │   ├── data.py
│   │   ├── filters.py
│   │   └── pagination.py
│   ├── services/          # Business logic
│   │   ├── app_service.py
│   │   └── data_service.py
│   ├── repositories/      # Data access layer
│   │   ├── app_repository.py
│   │   └── data_repository.py
│   ├── clients/           # External API clients
│   │   ├── qlik_engine.py
│   │   └── qlik_repository.py
│   ├── middleware/        # Custom middleware
│   │   ├── cors.py
│   │   └── logging.py
│   └── utils/             # Utility functions
│       ├── formatters.py
│       └── validators.py
├── tests/                 # Test suite
│   ├── conftest.py       # Pytest fixtures
│   ├── unit/             # Unit tests
│   │   └── test_services.py
│   └── integration/      # Integration tests
│       └── test_endpoints.py
├── certs/                # SSL certificates (gitignored)
├── .env                  # Environment variables (gitignored)
├── .env.example          # Example environment file
├── pyproject.toml        # Project configuration
├── requirements.txt      # Python dependencies
├── run.py               # Application entry point
└── README.md            # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run tests: `pytest tests/`
5. Format code: `black src/ tests/`
6. Commit changes: `git commit -m "Add my feature"`
7. Push to branch: `git push origin feature/my-feature`
8. Create Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check [Troubleshooting](#troubleshooting) section
- Review API documentation at `/docs`
- Check server logs with `LOG_LEVEL=DEBUG`
- Contact your Qlik Sense administrator for server issues

## Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Qlik Sense Engine API**: https://help.qlik.com/en-US/sense-developer/
- **Qlik Sense Repository API**: https://help.qlik.com/en-US/sense-developer/
- **Pydantic Documentation**: https://docs.pydantic.dev/

---

**Version**: 1.0.0
**Last Updated**: January 2026
**Status**: Production Ready
