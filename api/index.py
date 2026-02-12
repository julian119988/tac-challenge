"""Vercel serverless function entry point for FastAPI ADW automation server.

This module serves as the ASGI handler for Vercel's Python runtime, exposing
the FastAPI application from apps.adw_server.server for serverless deployment.

Vercel serverless functions require:
1. Function entry point in api/ or /api directory
2. ASGI application exported at module level
3. Proper path configuration for module imports

Environment Variables (must be set in Vercel dashboard):
    - GITHUB_WEBHOOK_SECRET (required)
    - ANTHROPIC_API_KEY (required)
    - ENVIRONMENT (default: production)
    - LOG_LEVEL (default: INFO)
    - ADW_DEFAULT_MODEL (default: sonnet)
    - CORS_ENABLED (default: true)

Usage:
    This file is automatically invoked by Vercel's Python runtime.
    All HTTP requests to the deployment are routed to the FastAPI app.
"""

import sys
import os

# Add project root to Python path for module imports
# In Vercel serverless environment, the working directory is the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add adw_server directory to path so core modules can be imported
adw_server_dir = os.path.join(project_root, "apps", "adw_server")
if adw_server_dir not in sys.path:
    sys.path.insert(0, adw_server_dir)

# Import the FastAPI application
# The app is already configured with all routes, middleware, and lifespan events
from apps.adw_server.server import app

# Export the app for Vercel's ASGI handler
# Vercel will automatically detect and use this as the ASGI application
__all__ = ["app"]
