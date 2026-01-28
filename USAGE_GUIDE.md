# Qlik Sense REST API - Usage Guide

## Quick Start

### 1. Start the Server

```bash
cd qlik-sense-api
./start_server.sh
```

The server will start at `http://localhost:8000`

### 2. Access API Documentation

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API Endpoints

### Health Check

Check if the API and Qlik Sense connection are healthy.

**Endpoint:** `GET /api/v1/health`

**Example:**
```bash
curl http://localhost:8000/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T09:00:00Z",
  "version": "1.0.0",
  "qlik_connection": "connected"
}
```

---

### List Applications

Get all available Qlik Sense applications configured in the API.

**Endpoint:** `GET /api/v1/apps`

**Example:**
```bash
curl http://localhost:8000/api/v1/apps
```

**Response:**
```json
{
  "apps": [
    {
      "app_name": "akfa-employees",
      "app_id": "5a730580-3c25-4805-a2ef-dd4a71a91cda",
      "display_name": "AKFA Company Employees",
      "description": null
    }
  ]
}
```

---

### List Tables in an App

Get all tables available in a specific application.

**Endpoint:** `GET /api/v1/apps/{app_name}/tables`

**Parameters:**
- `app_name` (path): Application name (e.g., "akfa-employees")

**Example:**
```bash
curl http://localhost:8000/api/v1/apps/akfa-employees/tables
```

**Response:**
```json
{
  "app_name": "akfa-employees",
  "tables": [
    {
      "table_name": "Employees",
      "field_count": 15,
      "estimated_rows": 500
    },
    {
      "table_name": "Departments",
      "field_count": 5,
      "estimated_rows": 20
    }
  ]
}
```

---

### Get Table Data (Main Endpoint)

Retrieve paginated data from a specific table with optional filtering and sorting.

**Endpoint:** `GET /api/v1/apps/{app_name}/tables/{table_name}`

**Path Parameters:**
- `app_name`: Application name
- `table_name`: Table name

**Query Parameters:**
- `page` (integer, default=1): Page number (min: 1)
- `page_size` (integer, default=100): Items per page (min: 1, max: 1000)
- `filter_field` (string, optional): Field to filter on
- `filter_value` (string, optional): Value to filter by
- `sort_field` (string, optional): Field to sort by
- `sort_order` (string, default="asc"): Sort order ("asc" or "desc")

---

## Usage Examples

### Example 1: Basic Pagination

Get first page with 50 records:

```bash
curl "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?page=1&page_size=50"
```

**Response:**
```json
{
  "app_name": "akfa-employees",
  "table_name": "Employees",
  "data": [
    {
      "EmployeeID": "001",
      "Name": "John Doe",
      "Department": "Sales",
      "Salary": 50000
    },
    {
      "EmployeeID": "002",
      "Name": "Jane Smith",
      "Department": "Engineering",
      "Salary": 75000
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_records": 500,
    "total_pages": 10,
    "has_next": true,
    "has_previous": false
  },
  "metadata": {
    "fields": ["EmployeeID", "Name", "Department", "Salary"],
    "query_time_ms": 245
  }
}
```

---

### Example 2: Filtering

Get employees in the Sales department:

```bash
curl "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?filter_field=Department&filter_value=Sales&page=1&page_size=20"
```

---

### Example 3: Sorting

Get employees sorted by salary in descending order:

```bash
curl "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?sort_field=Salary&sort_order=desc&page=1&page_size=10"
```

---

### Example 4: Combined Filtering and Sorting

Get Sales department employees sorted by name:

```bash
curl "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?filter_field=Department&filter_value=Sales&sort_field=Name&sort_order=asc&page=1&page_size=25"
```

---

### Example 5: Navigate to Next Page

```bash
# Page 1
curl "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?page=1&page_size=100"

# Page 2
curl "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?page=2&page_size=100"

# Page 3
curl "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?page=3&page_size=100"
```

---

## Using with Python

### Install requests

```bash
pip install requests
```

### Example Python Client

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# List apps
response = requests.get(f"{BASE_URL}/apps")
apps = response.json()["apps"]
print(f"Available apps: {[app['app_name'] for app in apps]}")

# Get table data with pagination
params = {
    "page": 1,
    "page_size": 50,
    "filter_field": "Department",
    "filter_value": "Sales",
    "sort_field": "Name",
    "sort_order": "asc"
}

response = requests.get(
    f"{BASE_URL}/apps/akfa-employees/tables/Employees",
    params=params
)

data = response.json()
print(f"Total records: {data['pagination']['total_records']}")
print(f"Current page: {data['pagination']['page']}")
print(f"Records on this page: {len(data['data'])}")

# Iterate through all pages
for record in data['data']:
    print(f"Employee: {record.get('Name')} - {record.get('Department')}")
```

---

## Using with JavaScript/TypeScript

### Example Fetch API

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Health check
async function checkHealth() {
  const response = await fetch(`${BASE_URL}/health`);
  const data = await response.json();
  console.log(data);
}

// Get table data
async function getEmployees(page = 1, pageSize = 50) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
    filter_field: 'Department',
    filter_value: 'Sales'
  });

  const response = await fetch(
    `${BASE_URL}/apps/akfa-employees/tables/Employees?${params}`
  );

  const data = await response.json();
  return data;
}

// Usage
checkHealth();

getEmployees(1, 50).then(data => {
  console.log(`Total records: ${data.pagination.total_records}`);
  console.log(`Current page: ${data.pagination.page}`);
  data.data.forEach(employee => {
    console.log(`${employee.Name} - ${employee.Department}`);
  });
});
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "Error message",
  "path": "/api/v1/apps/invalid-app/tables/test",
  "method": "GET"
}
```

### Common HTTP Status Codes

- **200 OK**: Successful request
- **400 Bad Request**: Invalid parameters
- **404 Not Found**: App or table not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Qlik Sense connection issue

### Example Error Handling (Python)

```python
import requests

try:
    response = requests.get(
        "http://localhost:8000/api/v1/apps/invalid-app/tables/test"
    )
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("App or table not found")
    elif e.response.status_code == 503:
        print("Qlik Sense connection unavailable")
    else:
        print(f"Error: {e.response.json()}")
```

---

## Adding New Apps

To add a new Qlik Sense application to the API:

1. Open `.env` file
2. Update `APP_MAPPINGS_JSON` with your app:

```env
APP_MAPPINGS_JSON={"akfa-employees": "5a730580-3c25-4805-a2ef-dd4a71a91cda", "my-new-app": "your-app-id-here"}
```

3. Restart the server:

```bash
./start_server.sh
```

---

## Performance Tips

1. **Use appropriate page sizes**:
   - Small requests: 10-50 records
   - Medium requests: 100-500 records
   - Large requests: 500-1000 records (max)

2. **Filter data when possible**:
   - Filtering reduces data transfer
   - Faster query execution
   - Lower memory usage

3. **Sort only when needed**:
   - Sorting adds overhead
   - Pre-sorted data is faster

4. **Cache responses**:
   - Metadata is cached for 5 minutes
   - Consider client-side caching for static data

---

## Troubleshooting

### Issue: "Qlik connection error"

**Solution:**
- Check if Qlik Sense server is accessible
- Verify certificate files in `./certs/`
- Check `.env` configuration (host, ports, credentials)

### Issue: "App not found"

**Solution:**
- Verify app name in `APP_MAPPINGS_JSON`
- Check if app ID is correct
- Use `GET /api/v1/apps` to list available apps

### Issue: "Table not found"

**Solution:**
- Use `GET /api/v1/apps/{app_name}/tables` to list available tables
- Verify table name spelling and case

### Issue: Slow responses

**Solution:**
- Reduce `page_size`
- Add filtering to limit data
- Check Qlik Sense server performance
- Review network latency

---

## Advanced Usage

### Pagination Loop (Python)

Get all records from a table:

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

def get_all_records(app_name, table_name, page_size=100):
    all_records = []
    page = 1

    while True:
        response = requests.get(
            f"{BASE_URL}/apps/{app_name}/tables/{table_name}",
            params={"page": page, "page_size": page_size}
        )
        data = response.json()

        all_records.extend(data['data'])

        if not data['pagination']['has_next']:
            break

        page += 1

    return all_records

# Usage
employees = get_all_records('akfa-employees', 'Employees', page_size=500)
print(f"Total employees fetched: {len(employees)}")
```

---

## Support

For issues and questions:
- Check the logs: Server outputs detailed logs
- Review `.env` configuration
- Verify Qlik Sense connectivity
- Check OpenAPI docs: http://localhost:8000/docs
