# Chore: Vercel Deployment Configuration

## Metadata
adw_id: `bb47b0ba`
prompt: `Lets add a vercel file to deploy app to vercel. Should indicate fastAPI init`

## Chore Description
Add Vercel deployment configuration to enable deploying the FastAPI ADW automation server to Vercel. This involves creating a `vercel.json` configuration file that properly specifies the FastAPI application entry point and configures the deployment settings for the serverless environment.

## Relevant Files
Use these files to complete the chore:

- **`apps/adw_server/server.py`** - Main FastAPI application (`app` object) that needs to be referenced in Vercel config
- **`apps/adw_server/main.py`** - Entry point with uvicorn setup (reference for understanding server initialization)
- **`requirements.txt`** - Python dependencies that Vercel will need to install
- **`.env.example`** - Environment variables template to understand required configuration
- **`apps/adw_server/.env.example`** - Server-specific environment variables needed for deployment

### New Files

- **`vercel.json`** - Vercel deployment configuration file (to be created at project root)
- **`api/index.py`** - Vercel serverless function entry point for FastAPI (to be created)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Vercel Configuration File
- Create `vercel.json` at the project root
- Configure the build settings to install Python dependencies from `requirements.txt`
- Set up routing rules to direct all requests to the FastAPI serverless function
- Configure environment variables placeholders for required secrets (GITHUB_WEBHOOK_SECRET, ANTHROPIC_API_KEY)
- Set Python runtime version (3.12 or compatible)

### 2. Create Vercel Serverless Function Entry Point
- Create `api/index.py` to serve as the Vercel serverless function handler
- Import the FastAPI `app` from `apps.adw_server.server`
- Export the app in a format compatible with Vercel's ASGI handler
- Handle any path adjustments needed for the serverless environment
- Ensure proper initialization of the FastAPI application

### 3. Update Documentation
- Add deployment instructions to the main `README.md`
- Document required environment variables in Vercel dashboard
- Include steps for connecting GitHub repository to Vercel
- Add notes about static file serving considerations in serverless environment
- Document any limitations or differences between local and Vercel deployment

### 4. Validate Configuration
- Review `vercel.json` syntax and structure
- Verify that all required dependencies are in `requirements.txt`
- Confirm that the FastAPI app initialization path is correct
- Check that environment variable references match `.env.example`
- Ensure routing configuration covers all FastAPI endpoints

## Validation Commands
Execute these commands to validate the chore is complete:

- `python -m json.tool vercel.json` - Validate vercel.json is valid JSON
- `python -c "from api.index import app; print(app)"` - Test that the Vercel entry point can import the FastAPI app successfully
- `python -m py_compile api/index.py` - Ensure the Vercel entry point compiles without syntax errors
- `grep -E "(GITHUB_WEBHOOK_SECRET|ANTHROPIC_API_KEY)" vercel.json` - Verify required environment variables are referenced in config

## Notes
- Vercel requires serverless functions to be in the `api/` or `/api` directory by default
- The FastAPI app must be exposed as an ASGI application for Vercel's Python runtime
- Static files (from `apps/frontend/dist`) may need separate configuration or should be served from Vercel's CDN
- Consider that the serverless environment may have different working directory assumptions than local development
- Environment variables must be configured in the Vercel dashboard; they won't be read from `.env` files
- The lifespan context manager in `server.py` should work correctly in serverless environment
