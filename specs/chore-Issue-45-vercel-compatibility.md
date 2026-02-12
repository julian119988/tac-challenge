# Chore: Vercel Compatibility

## Metadata
adw_id: `Issue #45`
prompt: `Lets add a vercel file to deploy app to vercel. Should indicate fastAPI init`

## Chore Description
Add Vercel deployment configuration to enable deploying the FastAPI ADW server to Vercel's serverless platform. This involves creating a `vercel.json` configuration file that properly routes requests to the FastAPI application and sets up the necessary build configuration for Python/FastAPI deployment on Vercel.

## Relevant Files
Use these files to complete the chore:

- `apps/adw_server/server.py` - Main FastAPI application that needs to be exposed to Vercel
- `apps/adw_server/main.py` - Entry point that will need to be referenced in Vercel configuration
- `requirements.txt` - Python dependencies that Vercel will need to install

### New Files
- `vercel.json` - Vercel configuration file to be created at project root
- `api/index.py` - Vercel serverless function entry point (optional, depending on approach)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Vercel Configuration File
- Create `vercel.json` at the project root
- Configure the build settings to specify Python runtime
- Set up routes to direct all requests to the FastAPI application
- Configure rewrites to handle the FastAPI app paths (root `/`, `/health`, `/webhooks/github`, etc.)
- Specify environment variables that need to be configured in Vercel dashboard

### 2. Create Vercel API Entry Point
- Create an `api/` directory at project root if using Vercel's API routes pattern
- Create `api/index.py` that imports and exposes the FastAPI app instance
- Ensure the entry point correctly references `apps.adw_server.server:app`
- Handle PYTHONPATH configuration so imports work correctly in Vercel's serverless environment

### 3. Update Dependencies Configuration
- Verify that `requirements.txt` includes all necessary dependencies for Vercel deployment
- Ensure FastAPI, uvicorn, pydantic, and other core dependencies are properly specified
- Add any Vercel-specific requirements if needed

### 4. Document Deployment Instructions
- Add deployment notes to help configure environment variables in Vercel
- Document the required environment variables (GITHUB_WEBHOOK_SECRET, ANTHROPIC_API_KEY, etc.)
- Include instructions for connecting GitHub repository to Vercel
- Note any limitations or differences when running on Vercel vs local development

### 5. Test Configuration Validity
- Validate that `vercel.json` has proper JSON syntax
- Verify that the FastAPI app can be imported correctly from the new entry point
- Ensure no breaking changes to local development workflow

## Validation Commands
Execute these commands to validate the chore is complete:

- `cat vercel.json` - Verify the Vercel configuration file exists and has correct syntax
- `python -m json.tool vercel.json` - Validate JSON syntax
- `python -c "from apps.adw_server.server import app; print('FastAPI app import successful')"` - Verify FastAPI app can be imported
- `uv run python -m py_compile apps/adw_server/*.py` - Ensure Python files compile without errors

## Notes
Vercel deployment requires:
1. A `vercel.json` configuration file that tells Vercel how to build and run the application
2. Proper routing configuration to direct HTTP requests to the FastAPI app
3. Environment variables must be configured in the Vercel dashboard (GITHUB_WEBHOOK_SECRET, ANTHROPIC_API_KEY)
4. The FastAPI app needs to be exposed as a WSGI/ASGI application for Vercel's serverless functions
5. Static file serving (for the camera app) may need special handling in Vercel's environment

The deployment will use Vercel's Python runtime with FastAPI running in serverless mode. This is different from the local uvicorn development server but should maintain the same functionality for the webhook endpoints and health checks.
