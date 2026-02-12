"""Vercel serverless function entry point for FastAPI ADW server.

This module serves as the entry point for Vercel's Python runtime.
It imports the FastAPI app instance and exposes it for serverless execution.

Vercel Configuration:
    This file is referenced in vercel.json as the build source.
    All HTTP requests are routed to this entry point.

Environment Variables Required:
    - GH_WB_SECRET: Secret for validating GitHub webhook signatures
    - ANTHROPIC_API_KEY: API key for Anthropic Claude integration
    - ADW_WORKING_DIR: Working directory for ADW operations (default: /tmp)
    - ENVIRONMENT: Deployment environment (default: production)

Note:
    In Vercel's serverless environment, the working directory is /tmp
    and the environment is ephemeral. ADW workflows will execute in
    this temporary environment.
"""

import sys
import os

# Set up Python path for imports to work in Vercel's serverless environment
# Vercel's working directory is the project root, but we need to ensure
# both the project root and adw_server are in the path

# Get the absolute path to the project root (parent of api/ directory)
current_file = os.path.abspath(__file__)
api_dir = os.path.dirname(current_file)
project_root = os.path.dirname(api_dir)

# Add project root first
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add adw_server directory so core modules can be imported directly
adw_server_dir = os.path.join(project_root, "apps", "adw_server")
if adw_server_dir not in sys.path:
    sys.path.insert(0, adw_server_dir)

# Import the FastAPI app instance
# This import will trigger config loading, which now handles serverless environments
from apps.adw_server.server import app

# Vercel expects the ASGI application to be named 'app'
# This is automatically detected and used by the @vercel/python runtime
__all__ = ["app"]
