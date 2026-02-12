#!/bin/bash
# Start the webhook server using uv (no Python install required)

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found in project root"
    echo "Please run: cp apps/adw_server/.env.example .env"
    echo "Then edit .env and set GH_WB_SECRET and ANTHROPIC_API_KEY"
    exit 1
fi

echo "Starting webhook server..."
echo "Server will be available at http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

PYTHONPATH=. uv run \
    --with fastapi \
    --with "uvicorn[standard]" \
    --with pydantic \
    --with pydantic-settings \
    --with python-dotenv \
    --with httpx \
    --with click \
    --with rich \
    uvicorn apps.adw_server.server:app --host 0.0.0.0 --port 8000
