# Chore: Vercel Compatibility

## Metadata
adw_id: `Issue #45`
prompt: `18f26952 Issue #45: Vercel compatibility

Lets add a vercel file to deploy app to vercel.

Should indicate fastAPI init`

## Chore Description
Add Vercel deployment configuration to enable serverless deployment of the FastAPI ADW automation server on Vercel's platform. This includes creating a `vercel.json` configuration file that specifies the Python build settings, routing rules, and environment variables, as well as creating a serverless function entry point (`api/index.py`) that properly initializes and exposes the FastAPI application for Vercel's ASGI handler.

## Relevant Files
Use these files to complete the chore:

- **`apps/adw_server/server.py`** - Main FastAPI application containing the `app` object that needs to be exposed for Vercel deployment
- **`apps/adw_server/main.py`** - Entry point that shows how the server is initialized with uvicorn (reference for understanding server setup)
- **`requirements.txt`** - Python dependencies list that Vercel will use to install packages in the serverless environment
- **`apps/adw_server/core/config.py`** - Configuration module that loads environment variables (needs to work in serverless environment)
- **`README.md`** - Project documentation that should include Vercel deployment instructions

### New Files

- **`vercel.json`** - Vercel deployment configuration file at project root specifying build settings, routing rules, and environment variables
- **`api/index.py`** - Vercel serverless function entry point that imports and exports the FastAPI app for ASGI handler

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Vercel Configuration File
- Create `vercel.json` at the project root
- Specify version 2 of Vercel configuration format
- Configure builds array with Python builder `@vercel/python` for `api/index.py`
- Set Python runtime to `python3.12`
- Set `maxLambdaSize` to `15mb` to accommodate dependencies
- Add routing rule to direct all requests `(.*)` to `api/index.py`
- Configure environment variables as Vercel secrets: `GITHUB_WEBHOOK_SECRET`, `ANTHROPIC_API_KEY`, `ENVIRONMENT`, `LOG_LEVEL`, `ADW_DEFAULT_MODEL`, `CORS_ENABLED`
- Set deployment region (e.g., `iad1` for US East)

### 2. Create Vercel Serverless Function Entry Point
- Create `api/` directory at project root
- Create `api/index.py` as the Vercel serverless function handler
- Add proper Python path configuration to enable imports from project modules
- Add project root to `sys.path` for module resolution
- Add `apps/adw_server` directory to `sys.path` for core module imports
- Import the FastAPI `app` from `apps.adw_server.server`
- Export the app at module level for Vercel's ASGI handler
- Add docstring explaining Vercel serverless function requirements and environment variables

### 3. Update README Documentation
- Add "Deployment to Vercel" section to README.md
- Document pre-requisites (Vercel account, GitHub repository connection)
- Provide step-by-step deployment instructions:
  1. Connecting repository to Vercel dashboard
  2. Configuring environment variables in Vercel project settings
  3. Deploying and obtaining deployment URL
  4. Configuring GitHub webhook with Vercel URL
- Document serverless limitations (execution time limits, stateless environment, working directory constraints)
- Note which ADW workflows may have limitations in serverless environment
- Include guidance on when to use traditional VPS/Docker deployment instead

### 4. Validate Vercel Configuration
- Verify `vercel.json` is valid JSON format
- Test that `api/index.py` can successfully import the FastAPI app
- Confirm Python compilation of the entry point
- Validate all required dependencies are in `requirements.txt`
- Check that environment variable references use Vercel secret syntax (`@secret_name`)

## Validation Commands
Execute these commands to validate the chore is complete:

- `python -m json.tool vercel.json` - Validate vercel.json is syntactically correct JSON
- `python -c "import sys; sys.path.insert(0, '.'); from api.index import app; print(f'FastAPI app loaded: {app}')"` - Test that the Vercel entry point successfully imports and exposes the FastAPI app
- `python -m py_compile api/index.py` - Ensure the Vercel serverless function entry point compiles without syntax errors
- `grep -E '(GITHUB_WEBHOOK_SECRET|ANTHROPIC_API_KEY|ENVIRONMENT)' vercel.json` - Verify required environment variables are configured in vercel.json
- `grep -E 'fastapi|uvicorn|pydantic|python-dotenv' requirements.txt` - Confirm all essential FastAPI and configuration dependencies are present
- `test -f vercel.json && test -f api/index.py && echo "Required Vercel files exist"` - Verify both required files are created

## Notes
- Vercel serverless functions have execution time limits: 10 seconds on free tier, 60 seconds on Pro tier
- The serverless environment is stateless - no file persistence between invocations
- ADW workflows that require git operations, file creation, or long-running tasks may need adjustments for serverless constraints
- Environment variables must be configured in Vercel dashboard as project settings, not in .env files
- The FastAPI app's lifespan context manager handles startup/shutdown events even in serverless environment
- Static files (if any) should be placed in public/ directory for Vercel CDN serving
- Consider using traditional server deployment (VPS, Docker) for complex ADW workflows requiring extended execution time or persistent file system
- The `@vercel/python` builder automatically installs dependencies from requirements.txt during deployment
