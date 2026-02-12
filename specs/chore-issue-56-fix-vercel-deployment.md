# Chore: Fix Vercel Deployment Import Error

## Metadata
adw_id: `Issue #56`
prompt: `Vercel deploy was successful but I get this error when I try to load the page: "Error importing api/index.py: Traceback (most recent call last): File "/var/task/_vendor/vercel_runtime/vc_init.py", line 238, in <module> __vc_spec.loader.exec_module(__vc_module) File "<frozen importlib._bootstrap_external>", line 999, in exec_module File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed F..."`

## Chore Description
The Vercel deployment builds successfully but fails at runtime with an import error when loading `api/index.py`. The error occurs in Vercel's Python runtime during module loading. This is a critical issue preventing the application from running in production.

The likely causes are:
1. **Import path issues in Vercel's serverless environment**: The `api/index.py` file tries to import from `apps.adw_server.server` and `core` modules, but the Python path manipulation may not work correctly in Vercel's runtime
2. **Missing or incorrect dependencies**: Required packages may not be properly specified in `requirements.txt`
3. **Environment configuration issues**: Missing or incorrectly set environment variables in Vercel
4. **Module structure incompatibility**: The nested module structure (`apps/adw_server/core`) may not work as expected in Vercel's serverless environment

The fix should ensure that all imports resolve correctly in Vercel's serverless Python environment where the file system structure and Python path behavior differ from local development.

## Relevant Files
Use these files to complete the chore:

- **`api/index.py`** (lines 22-37): Contains the problematic import logic that sets up Python paths and imports the FastAPI app. This is the entry point for Vercel's Python runtime
- **`vercel.json`**: Configures Vercel build and routing. Currently routes all requests to `api/index.py`
- **`requirements.txt`**: Lists Python dependencies. May be missing packages needed by the application
- **`apps/adw_server/server.py`** (lines 36-61): The FastAPI application that `api/index.py` tries to import. Contains its own path manipulation logic
- **`apps/adw_server/core/__init__.py`**: Core module initialization that imports from submodules. These imports must succeed for the server to start
- **`apps/adw_server/core/config.py`** (lines 123-155): Configuration module with validators that check directory existence, which may fail in Vercel's environment
- **`VERCEL_DEPLOYMENT.md`**: Deployment guide documenting the expected setup

### New Files
- **`.vercelignore`** (optional): May need to be created to exclude unnecessary files from deployment if deployment size is an issue

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Diagnose the Import Error
- Read the full Vercel deployment logs to see the complete error traceback (not just the truncated version)
- Check Vercel Function logs in the dashboard to understand which specific import is failing
- Verify the deployed file structure in Vercel to ensure all required files are present

### 2. Fix Environment Variable Issues
- Verify that required environment variables are set in Vercel dashboard (especially `GH_WB_SECRET`, `ANTHROPIC_API_KEY`)
- Add `ADW_WORKING_DIR=/tmp` to Vercel environment variables (Vercel's serverless environment requires `/tmp` for writable storage)
- Ensure `ENVIRONMENT=production` is set to skip directory validation that may fail in serverless environment

### 3. Update Configuration for Serverless Environment
- Modify `apps/adw_server/core/config.py` to handle serverless environment:
  - Make `adw_working_dir` validator more lenient for production/serverless environments
  - Make `static_files_dir` validator handle missing directories gracefully in serverless
  - Consider using environment checks to skip filesystem validation in Vercel

### 4. Fix Import Path Issues in api/index.py
- Review and update the Python path manipulation in `api/index.py` (lines 22-34)
- Ensure that both `project_root` and `adw_server_dir` are added to `sys.path` correctly
- Test that the import statement `from apps.adw_server.server import app` works in Vercel's environment
- Consider simplifying imports or restructuring to avoid complex path manipulation

### 5. Verify Dependencies in requirements.txt
- Ensure all required packages are listed with appropriate versions
- Add any missing dependencies discovered during error diagnosis
- Verify that transitive dependencies are satisfied

### 6. Update vercel.json Configuration
- Review the build configuration in `vercel.json`
- Consider adding build configuration options if needed (e.g., Python version specification)
- Ensure routing configuration is correct

### 7. Test Locally with Vercel CLI
- Install Vercel CLI: `npm install -g vercel`
- Run `vercel dev` locally to simulate Vercel's environment
- Verify that the application starts without import errors
- Test the `/health` and `/health/ready` endpoints

### 8. Deploy and Validate
- Deploy the fixes to Vercel (either via git push or `vercel deploy`)
- Monitor Vercel Function logs during deployment
- Test all endpoints after deployment:
  - `GET /health` - should return `{"status": "ok"}`
  - `GET /health/ready` - should return `{"status": "ready"}` or identify specific issues
  - `GET /app` - should serve the frontend application
- Document any Vercel-specific configuration in `VERCEL_DEPLOYMENT.md`

## Validation Commands
Execute these commands to validate the chore is complete:

- `vercel logs --follow` - Monitor Vercel deployment logs and verify no import errors
- `curl https://your-deployment-url.vercel.app/health` - Should return 200 OK with status "ok"
- `curl https://your-deployment-url.vercel.app/health/ready` - Should return 200 OK with status "ready"
- `curl https://your-deployment-url.vercel.app/app` - Should return the HTML for the frontend app
- Check Vercel dashboard → Deployments → Latest deployment → Function logs - Should show successful startup without import errors

## Notes
- Vercel's serverless Python environment has important differences from local development:
  - Working directory is read-only except for `/tmp`
  - File system is ephemeral (resets between invocations)
  - Cold start behavior means imports happen on every cold start
  - Python path behavior may differ from local environment

- The error message is truncated in the prompt, so the first step of reading the full logs is critical to understanding the exact failure point

- If the issue persists after fixes, consider:
  - Creating a minimal reproducible example to test imports
  - Checking if there are circular imports in the module structure
  - Reviewing Vercel's Python runtime version compatibility

- The configuration validators in `config.py` that check for directory existence may need to be disabled or made more lenient for the serverless environment where certain directories may not exist or be relevant
