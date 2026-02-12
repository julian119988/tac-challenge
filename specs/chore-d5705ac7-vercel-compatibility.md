# Chore: Vercel Compatibility

## Metadata
adw_id: `d5705ac7`
prompt: `Issue #45: Vercel compatibility

Lets add a vercel file to deploy app to vercel.

Should indicate fastAPI init`

## Chore Description
Add and validate Vercel deployment configuration to ensure the FastAPI ADW automation server can be deployed to Vercel's serverless platform. This involves verifying the `vercel.json` configuration file correctly specifies the FastAPI application entry point, ensuring proper serverless function setup, and validating that all required dependencies and environment variables are configured for successful deployment.

## Relevant Files
Use these files to complete the chore:

- **`apps/adw_server/server.py:455-469`** - Main FastAPI application with the `app` object that needs to be referenced in Vercel config
- **`apps/adw_server/main.py:28-48`** - Entry point with uvicorn setup (reference for understanding server initialization)
- **`requirements.txt`** - Python dependencies that Vercel will need to install
- **`apps/adw_server/.env.example`** - Server-specific environment variables template showing required configuration
- **`README.md:124-168`** - Existing Vercel deployment documentation
- **`vercel.json`** - Existing Vercel deployment configuration file
- **`api/index.py`** - Existing Vercel serverless function entry point for FastAPI

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Verify Vercel Configuration File
- Review existing `vercel.json` at the project root
- Confirm build settings reference correct Python runtime and FastAPI entry point (`api/index.py`)
- Validate routing rules direct all requests to the FastAPI serverless function
- Verify environment variable placeholders are configured (GITHUB_WEBHOOK_SECRET, ANTHROPIC_API_KEY, ENVIRONMENT, LOG_LEVEL, ADW_DEFAULT_MODEL, CORS_ENABLED)
- Ensure Python runtime version is set to 3.12
- Confirm maxLambdaSize is set appropriately (15mb)
- Verify region configuration is set correctly

### 2. Verify Vercel Serverless Function Entry Point
- Review `api/index.py` serverless function handler
- Confirm it correctly imports the FastAPI `app` from `apps.adw_server.server`
- Verify the app is exported properly for Vercel's ASGI handler
- Check path adjustments are correct for the serverless environment
- Ensure proper module path configuration (project_root and adw_server_dir in sys.path)

### 3. Validate Dependencies
- Review `requirements.txt` to ensure all FastAPI dependencies are included
- Verify fastapi, uvicorn[standard], pydantic, pydantic-settings, python-dotenv are present
- Ensure httpx is available for async HTTP operations
- Confirm all ADW module dependencies (click, rich) are listed

### 4. Verify Documentation
- Review deployment instructions in `README.md:124-168`
- Confirm environment variable setup instructions are complete
- Verify GitHub webhook configuration steps are documented
- Check that serverless limitations are clearly documented
- Ensure deployment steps are clear and accurate

### 5. Test Configuration Locally
- Validate `vercel.json` JSON syntax
- Test import of FastAPI app from Vercel entry point
- Verify Python compilation of `api/index.py`
- Confirm environment variable references are correct

## Validation Commands
Execute these commands to validate the chore is complete:

- `python -m json.tool vercel.json` - Validate vercel.json is valid JSON
- `python -c "import sys; sys.path.insert(0, '.'); from api.index import app; print(f'FastAPI app loaded: {app}')"` - Test that the Vercel entry point can import the FastAPI app successfully
- `python -m py_compile api/index.py` - Ensure the Vercel entry point compiles without syntax errors
- `grep -E '(GITHUB_WEBHOOK_SECRET|ANTHROPIC_API_KEY|ENVIRONMENT)' vercel.json` - Verify required environment variables are referenced in config
- `grep -E 'fastapi|uvicorn|pydantic' requirements.txt` - Confirm core FastAPI dependencies are in requirements.txt

## Notes
- The Vercel configuration uses `@vercel/python` builder for Python 3.12 runtime
- Serverless functions in Vercel have execution time limits (10s free tier, 60s Pro)
- Static files from `apps/frontend/dist` are served separately by Vercel's CDN
- Environment variables must be configured in the Vercel dashboard as secrets
- The FastAPI app's lifespan context manager handles startup/shutdown in serverless environment
- All routes are configured to proxy through `api/index.py` via the routing rule `"src": "/(.*)", "dest": "api/index.py"`
- ADW workflows that require git operations, file creation, or long-running tasks may have limitations in serverless environment
