#!/bin/bash

# Qlik Sense REST API Startup Script
# This script sets up the environment and starts the FastAPI server

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Qlik Sense REST API Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.example to .env and configure it.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found .env configuration file"

# Check if certificates exist
if [ ! -f ./certs/client.pem ]; then
    echo -e "${RED}Error: Certificate files not found in ./certs/${NC}"
    echo -e "${YELLOW}Please ensure client.pem, client_key.pem, and root.pem are in the certs directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found certificate files"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}No virtual environment found. Creating one...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -e .

echo -e "${GREEN}✓${NC} Dependencies installed"

# Load environment variables (using set -a to auto-export)
echo -e "${BLUE}Loading environment variables...${NC}"
set -a
source .env
set +a

# Display configuration
echo ""
echo -e "${BLUE}Server Configuration:${NC}"
echo -e "  Host: ${HOST:-0.0.0.0}"
echo -e "  Port: ${PORT:-8000}"
echo -e "  Debug: ${DEBUG:-false}"
echo -e "  Log Level: ${LOG_LEVEL:-INFO}"
echo ""
echo -e "${BLUE}Qlik Sense Configuration:${NC}"
echo -e "  Server: ${QLIK_SENSE_SCHEME}://${QLIK_SENSE_HOST}"
echo -e "  User: ${QLIK_USER_DIRECTORY}\\${QLIK_USER_ID}"
echo ""

# Start the server
echo -e "${GREEN}Starting FastAPI server...${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Server will be available at:${NC}"
echo -e "${GREEN}  http://${HOST:-0.0.0.0}:${PORT:-8000}${NC}"
echo -e "${BLUE}  API Documentation:${NC}"
echo -e "${GREEN}  http://${HOST:-0.0.0.0}:${PORT:-8000}/docs${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Run the server
python run.py
