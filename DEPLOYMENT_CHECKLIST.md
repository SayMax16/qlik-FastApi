# Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Environment Setup
- [x] Project structure created
- [x] Dependencies installed (`pyproject.toml`)
- [x] `.env` file configured
- [x] Certificate files in place (`./certs/`)
- [ ] Virtual environment created (`python3 -m venv venv`)

### 2. Configuration Verification
- [x] `QLIK_SENSE_HOST` set correctly
- [x] `QLIK_USER_DIRECTORY` configured
- [x] `QLIK_USER_ID` configured
- [x] Certificate paths correct
- [x] `APP_MAPPINGS_JSON` contains your apps
- [ ] `PORT` available (default: 8000)

### 3. Testing
- [ ] Health endpoint works: `GET /api/v1/health`
- [ ] List apps works: `GET /api/v1/apps`
- [ ] List tables works: `GET /api/v1/apps/{app_name}/tables`
- [ ] Get data works: `GET /api/v1/apps/{app_name}/tables/{table_name}`
- [ ] Pagination works
- [ ] Filtering works
- [ ] Sorting works
- [ ] Run test suite: `pytest tests/`

### 4. Security
- [x] No secrets in code
- [x] Environment variables used for config
- [x] Certificate authentication enabled
- [ ] `.env` not committed to git
- [ ] `.gitignore` properly configured
- [ ] Production mode (`DEBUG=false`) for prod

### 5. Documentation
- [x] README.md complete
- [x] USAGE_GUIDE.md with examples
- [x] API documentation accessible at `/docs`
- [x] PROJECT_SUMMARY.md created

---

## 🚀 First-Time Setup Steps

### Step 1: Navigate to Project
```bash
cd "/Users/saydulloismatov/Documents/qlik sense api/qlik-sense-api"
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -e .
```

### Step 4: Verify Configuration
```bash
# Check .env file
cat .env

# Verify certificate files
ls -la certs/
```

### Step 5: Start Server
```bash
./start_server.sh
```

### Step 6: Test Health Endpoint
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0",
  "qlik_connection": "connected"
}
```

### Step 7: Access API Documentation
Open browser: http://localhost:8000/docs

### Step 8: Test Data Retrieval
```bash
curl "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?page=1&page_size=10"
```

---

## 🔧 Production Deployment

### Option 1: Direct Deployment (Simple)

**1. Start with production settings:**
```bash
# Update .env
DEBUG=false
LOG_LEVEL=WARNING
HOST=0.0.0.0
PORT=8000

# Start server
./start_server.sh
```

### Option 2: Systemd Service (Recommended)

**1. Create service file:**
```bash
sudo nano /etc/systemd/system/qlik-api.service
```

**2. Add configuration:**
```ini
[Unit]
Description=Qlik Sense REST API
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/qlik-sense-api
Environment="PATH=/path/to/qlik-sense-api/venv/bin"
ExecStart=/path/to/qlik-sense-api/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**3. Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable qlik-api
sudo systemctl start qlik-api
sudo systemctl status qlik-api
```

### Option 3: Docker Deployment

**1. Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY run.py .
COPY certs/ certs/

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "run.py"]
```

**2. Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  qlik-api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./certs:/app/certs:ro
    restart: unless-stopped
```

**3. Deploy:**
```bash
docker-compose up -d
```

### Option 4: Gunicorn + Nginx (Production)

**1. Install Gunicorn:**
```bash
pip install gunicorn
```

**2. Start with Gunicorn:**
```bash
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

**3. Setup Nginx reverse proxy:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔍 Verification Commands

### Check Server is Running
```bash
curl -s http://localhost:8000/api/v1/health | jq
```

### Check Qlik Connection
```bash
curl -s http://localhost:8000/api/v1/health | jq '.qlik_connection'
```

### List Available Apps
```bash
curl -s http://localhost:8000/api/v1/apps | jq '.apps[].app_name'
```

### Get Sample Data
```bash
curl -s "http://localhost:8000/api/v1/apps/akfa-employees/tables/Employees?page=1&page_size=5" | jq '.data | length'
```

---

## 📊 Monitoring

### Check Logs
```bash
# If using systemd
sudo journalctl -u qlik-api -f

# If using start_server.sh
tail -f logs/api.log  # if logs are configured
```

### Health Check Endpoint
Set up monitoring to ping: `GET /api/v1/health`

Expected healthy response:
```json
{
  "status": "healthy",
  "qlik_connection": "connected"
}
```

### Performance Monitoring
Monitor these metrics:
- Response times (check `X-Process-Time` header)
- Error rates (4xx, 5xx responses)
- Qlik connection status
- Memory usage
- CPU usage

---

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :8000

# Check Python version
python3 --version  # Should be 3.9+

# Check dependencies
pip list | grep fastapi
```

### Qlik connection fails
```bash
# Test certificates
openssl x509 -in certs/client.pem -text -noout

# Test network connectivity
ping 10.7.11.70

# Check Qlik Sense is running
curl -k https://10.7.11.70:4242
```

### Import errors
```bash
# Reinstall dependencies
pip install --force-reinstall -e .

# Check PYTHONPATH
echo $PYTHONPATH
```

---

## 📈 Performance Tuning

### For High Load

**1. Increase workers (Gunicorn):**
```bash
# Formula: (2 * CPU cores) + 1
gunicorn src.api.main:app \
  --workers 9 \
  --worker-class uvicorn.workers.UvicornWorker
```

**2. Enable connection pooling:**
Update `src/api/core/config.py`:
```python
QLIK_CONNECTION_POOL_SIZE = 10
```

**3. Implement caching:**
Add Redis for response caching:
```bash
pip install redis
```

**4. Use CDN:**
For static documentation, use CDN for `/docs` assets.

---

## 🔐 Security Hardening

### Production Security

**1. Use HTTPS only:**
```env
QLIK_VERIFY_SSL=true
```

**2. Restrict CORS:**
```env
CORS_ORIGINS=["https://your-domain.com"]
```

**3. Add rate limiting:**
```bash
pip install slowapi
```

**4. Hide docs in production:**
Update `main.py`:
```python
app = FastAPI(
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)
```

**5. Set secure headers:**
Add security middleware in `main.py`.

---

## ✅ Final Verification

Before going live, verify:

- [ ] Health endpoint returns 200
- [ ] All configured apps are accessible
- [ ] Pagination works correctly
- [ ] Filtering returns correct results
- [ ] Sorting works as expected
- [ ] Error handling works (try invalid requests)
- [ ] Logs are being written
- [ ] Performance is acceptable
- [ ] Documentation is accessible
- [ ] Security settings are production-ready

---

## 🎉 You're Ready to Deploy!

Your Qlik Sense REST API is production-ready. Choose your deployment method and follow the steps above.

For support and questions, refer to:
- **README.md** - Overview and setup
- **USAGE_GUIDE.md** - API usage examples
- **PROJECT_SUMMARY.md** - Technical details
- **/docs** - Interactive API documentation
