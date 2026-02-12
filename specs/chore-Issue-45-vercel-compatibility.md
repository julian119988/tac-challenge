# Chore: Vercel Compatibility

## Metadata
adw_id: `Issue #45`
prompt: `Lets add a vercel file to deploy app to vercel. Should indicate fastAPI init`

## Chore Description
Add Vercel deployment configuration to enable deploying the FastAPI ADW server to Vercel's serverless platform. This involves creating a `vercel.json` configuration file that properly routes requests to the FastAPI application and sets up the necessary build configuration for Python/FastAPI deployment on Vercel.

The configuration should properly initialize and expose the FastAPI application for Vercel's Python runtime.

## Relevant Files
Use these files to complete the chore:

- `apps/adw_server/server.py` - Main FastAPI application (app instance) that needs to be exposed to Vercel
- `apps/adw_server/main.py` - Entry point for local development
- `requirements.txt` - Python dependencies that Vercel will install during build
- `apps/adw_server/core/config.py` - Configuration module for environment variables
- `apps/adw_server/core/handlers.py` - Webhook handlers for GitHub events

### New Files
- `vercel.json` - Vercel configuration file at project root
- `api/index.py` - Vercel serverless function entry point that imports and exposes FastAPI app
- `VERCEL_DEPLOYMENT.md` - Comprehensive deployment and troubleshooting guide

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Vercel Configuration File
- Create `vercel.json` at the project root
- Configure version 2 (latest Vercel configuration format)
- Set up builds array with Python runtime configuration
  - Specify `api/index.py` as the source file
  - Use `@vercel/python` builder
- Configure routes to direct all requests to the FastAPI API handler
  - Route pattern: `/(.*)`
  - Destination: `api/index.py`
- Define environment variables that need to be configured in Vercel dashboard
  - GH_WB_SECRET (using Vercel secrets)
  - ANTHROPIC_API_KEY (using Vercel secrets)
  - ADW_WORKING_DIR (set to `/tmp` for serverless environment)
  - SERVER_HOST, SERVER_PORT, ENVIRONMENT

### 2. Create Vercel API Entry Point
- Create `api/` directory at project root
- Create `api/index.py` that serves as the ASGI entry point for Vercel
- Configure Python path to ensure imports work correctly
  - Add project root to sys.path
  - Add adw_server directory to sys.path
- Import the FastAPI app instance from `apps.adw_server.server`
- Export the app instance so Vercel's Python runtime can detect it
- Add documentation explaining the Vercel serverless environment requirements

### 3. Verify Dependencies Configuration
- Review `requirements.txt` to ensure all dependencies are included
- Confirm FastAPI, uvicorn[standard], pydantic, pydantic-settings are specified
- Verify python-dotenv, httpx, click, rich are present
- Ensure no development-only dependencies will cause issues in production

### 4. Create Deployment Documentation
- Create `VERCEL_DEPLOYMENT.md` with comprehensive deployment guide
- Document prerequisites (Vercel account, GitHub connection)
- Provide step-by-step deployment instructions
  - Repository connection
  - Environment variable configuration (required and optional)
  - Deploy button workflow
- Add GitHub webhook configuration instructions
- Include testing procedures (health check, readiness check, webhook test)
- Document Vercel-specific considerations
  - Serverless environment limitations
  - Ephemeral filesystem (/tmp)
  - Execution time limits
  - Cold start behavior
  - Static file serving
- Add troubleshooting section for common issues
  - Import errors
  - Webhook signature validation
  - ADW workflow triggers
  - Timeout errors
- Include monitoring guidance (Vercel dashboard, GitHub webhook deliveries)
- Add sections for custom domains, updating, and rolling back deployments

### 5. Test Configuration Validity
- Validate `vercel.json` has correct JSON syntax
- Verify the FastAPI app can be imported from the api/index.py entry point
- Ensure no breaking changes to local development workflow
- Test that all required files are accessible in the deployment structure

## Validation Commands
Execute these commands to validate the chore is complete:

- `cat vercel.json` - Verify the Vercel configuration file exists
- `python -m json.tool vercel.json` - Validate JSON syntax is correct
- `python -c "import sys; sys.path.insert(0, 'apps/adw_server'); from apps.adw_server.server import app; print('✓ FastAPI app import successful')"` - Verify FastAPI app can be imported
- `uv run python -m py_compile apps/adw_server/*.py` - Ensure all Python files compile without errors
- `uv run python -m py_compile api/index.py` - Ensure Vercel entry point compiles
- `ls -la api/index.py vercel.json VERCEL_DEPLOYMENT.md` - Confirm all new files exist

## Notes

### Vercel Deployment Requirements
1. A `vercel.json` configuration file that tells Vercel how to build and run the application
2. Proper routing configuration to direct HTTP requests to the FastAPI app via api/index.py
3. Environment variables must be configured in the Vercel dashboard (GH_WB_SECRET, ANTHROPIC_API_KEY)
4. The FastAPI app needs to be exposed as an ASGI application for Vercel's serverless functions
5. Python path manipulation in api/index.py to ensure proper imports in serverless environment

### FastAPI Initialization for Vercel
The FastAPI app instance is already initialized in `apps/adw_server/server.py` with:
- Application metadata (title, description, version)
- Lifespan context manager for startup/shutdown events
- CORS middleware configuration
- Request logging middleware
- Route handlers for webhooks and health checks
- Static file mounting for the camera app

The `api/index.py` entry point simply imports this existing app instance and exposes it to Vercel's Python runtime, which automatically detects the ASGI application.

### Deployment Environment
The deployment will use Vercel's Python runtime with FastAPI running in serverless mode. This differs from the local uvicorn development server:
- Serverless functions have execution time limits (10s Hobby, 60s Pro)
- Filesystem is ephemeral (/tmp only)
- Cold starts on first request after idle period
- No persistent state between invocations

However, the webhook endpoints and health checks maintain full functionality.

### Static File Serving
The camera app frontend (React) is served from `apps/camera_app/dist`:
- `/app` route serves the React application via StaticFiles
- `/static` route serves legacy static files
- Static files are included in the Vercel deployment package
- FastAPI's StaticFiles middleware handles requests in serverless environment
