# Docker Deployment Guide

This guide explains how to build and run the Qlik Sense REST API using Docker.

## Prerequisites

- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)
- Qlik Sense certificates in the `certs/` directory
- `.env` file configured with your Qlik Sense settings

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### 2. Build and Run with Docker (without compose)

```bash
# Build the image
docker build -t qlik-sense-api:latest .

# Run the container
docker run -d \
  --name qlik-sense-api \
  -p 8000:8000 \
  -v $(pwd)/certs:/app/certs:ro \
  -v $(pwd)/.env:/app/.env:ro \
  qlik-sense-api:latest

# View logs
docker logs -f qlik-sense-api

# Stop the container
docker stop qlik-sense-api
docker rm qlik-sense-api
```

## Environment Configuration

The application reads configuration from the `.env` file. Make sure to:

1. Copy `.env.example` to `.env`
2. Update Qlik Sense connection details
3. Place certificates in the `certs/` directory

## Certificate Setup

Ensure your certificates are in the `certs/` directory:

```
certs/
├── client.pem       # Client certificate
├── client_key.pem   # Client private key
└── root.pem         # Root CA certificate
```

## Container Management

### View Container Status

```bash
docker-compose ps
```

### View Logs

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Container

```bash
docker-compose restart
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up -d --build

# Force rebuild
docker-compose build --no-cache
docker-compose up -d
```

## Health Check

The container includes a health check that runs every 30 seconds:

```bash
# Check health status
docker inspect qlik-sense-api | grep -A 10 Health
```

## Accessing the API

Once running, the API is available at:

- **API Base URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Troubleshooting

### Container won't start

Check logs for errors:
```bash
docker-compose logs qlik-api
```

### Certificate errors

Ensure certificates are mounted correctly:
```bash
docker exec qlik-sense-api ls -la /app/certs
```

### Connection to Qlik Sense fails

Verify environment variables:
```bash
docker exec qlik-sense-api env | grep QLIK
```

### Port already in use

Change the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change 8001 to any available port
```

## Production Deployment

For production deployment:

1. Use environment-specific `.env` files
2. Consider using Docker secrets for sensitive data
3. Set up proper logging and monitoring
4. Use a reverse proxy (nginx, traefik) for HTTPS
5. Configure resource limits in `docker-compose.yml`:

```yaml
services:
  qlik-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Updating the Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

## Cleaning Up

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove images
docker rmi qlik-sense-api:latest
```
