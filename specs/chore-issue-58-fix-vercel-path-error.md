# Chore: Fix Vercel deployment path error

## Metadata
adw_id: `Issue #58`
prompt: `When I load the page on vercel I see this error {"error":"Not Found","message":"Path not found: /app/"}

Could be that is trying to access app instead of apps?`

## Chore Description

The Vercel deployment is returning a 404 error when accessing `/app/` with the message `"Path not found: /app/"`. The issue is that the static files are being mounted from `apps/frontend` (which is correct) but the error handler is showing the incorrect path format.

Upon investigation, the root cause is:

1. **Static Files Configuration**: The `static_files_dir` in `config.py` defaults to `apps/frontend` (line 73)
2. **Static Mount in server.py**: The code attempts to mount the directory at `/app` (line 413)
3. **Path Resolution**: The config validator converts relative paths to absolute paths using `PROJECT_ROOT` (line 197 in config.py)
4. **Vercel Environment**: In Vercel's serverless environment, the static files directory is being set to `/tmp/static` via `vercel.json` (line 18)

The actual issue appears to be that:
- In local development, static files are at `apps/frontend/` (correct)
- In Vercel deployment, the environment variable `STATIC_FILES_DIR=/tmp/static` doesn't contain the actual static files
- The static files need to be either:
  1. Copied to `/tmp/static` at runtime, OR
  2. The configuration needs to point to the deployed location of `apps/frontend/`, OR
  3. Vercel needs to serve static files separately from the Python app

Based on the VERCEL_DEPLOYMENT.md documentation (line 174-177), static files should be included in the deployment and served from the `/app` route. However, the Vercel configuration is overriding the path to `/tmp/static` which may not exist.

## Relevant Files

Use these files to complete the chore:

- **vercel.json** - Vercel deployment configuration. Currently sets `STATIC_FILES_DIR=/tmp/static` which may not contain the actual frontend files. Need to either remove this override or update the deployment to copy files.

- **apps/adw_server/core/config.py** - Server configuration management. The `static_files_dir` field defaults to `apps/frontend` (line 73), and the validator handles serverless environments gracefully (lines 186-241). The `validate_static_dir` already handles missing directories in serverless environments.

- **apps/adw_server/server.py** - FastAPI server that mounts static files. Lines 408-427 handle mounting static files with error handling. The mount happens at `/app` which is correct.

- **api/index.py** - Vercel serverless entry point. This is the entry point for Vercel deployment and handles import path setup.

- **apps/frontend/** - Directory containing the actual frontend static files (index.html, app.js, styles.css, etc.) that need to be served at `/app/`.

### New Files
None needed - this is a configuration fix.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Investigate Current Vercel Deployment Structure
- Check if `apps/frontend/` files are actually deployed to Vercel
- Verify the filesystem structure in Vercel's serverless environment
- Confirm whether static files exist at deployment time or need to be accessed from a different location

### 2. Fix Static Files Path Configuration
- **Option A (Recommended)**: Remove or update `STATIC_FILES_DIR` override in `vercel.json` to point to the actual location of deployed frontend files
  - If frontend files are deployed with the app, use relative path `apps/frontend`
  - If they need to be in `/tmp`, ensure build process copies them there
- **Option B**: Configure Vercel to serve frontend files separately from the Python app using Vercel's native static file serving
  - Update `vercel.json` to include static file routing
  - May require adding `outputDirectory` configuration

### 3. Update vercel.json Configuration
- Review and update the `STATIC_FILES_DIR` environment variable
- Ensure the path points to where frontend files actually exist in deployment
- Consider whether `/tmp/static` is appropriate or if we should use the bundled `apps/frontend`
- Add any necessary build or routing configuration for static files

### 4. Test Static File Access
- Deploy the changes to Vercel
- Test accessing `/app/` endpoint
- Verify frontend files (index.html, app.js, styles.css) are served correctly
- Check Vercel logs for any static file mounting errors

### 5. Verify Root Redirect Works
- Test that accessing `/` redirects to `/app`
- Ensure the redirect is functional with the static file changes
- Confirm no 404 errors when accessing the application

### 6. Update Documentation if Needed
- If the fix requires changes to deployment process, update VERCEL_DEPLOYMENT.md
- Document any new environment variable requirements
- Add troubleshooting guidance for this specific issue

## Validation Commands

Execute these commands to validate the chore is complete:

- `curl https://your-vercel-deployment.vercel.app/` - Should redirect to `/app`
- `curl https://your-vercel-deployment.vercel.app/app/` - Should return the HTML frontend (not 404 error)
- `curl https://your-vercel-deployment.vercel.app/health` - Should return `{"status":"ok","service":"adw-webhook-server","environment":"production"}`
- Check Vercel deployment logs for any errors related to static file mounting
- Verify in browser that the Focus Keeper app loads correctly at the `/app/` endpoint

## Notes

**Key Insight**: The issue is likely that `vercel.json` is setting `STATIC_FILES_DIR=/tmp/static` but nothing is copying the frontend files from `apps/frontend/` to `/tmp/static/` during the build or runtime. Vercel's filesystem is read-only except for `/tmp`, so we either need to:

1. Let the Python app serve files from the bundled `apps/frontend/` directory (requires removing the `/tmp/static` override), OR
2. Copy files to `/tmp/static` during the Vercel build phase, OR
3. Configure Vercel to serve static files independently of the Python app (recommended for serverless)

**Recommended Solution**: Remove `STATIC_FILES_DIR` from `vercel.json` env variables and let it default to `apps/frontend`, which should be included in the Vercel deployment bundle. The config validator already handles this path correctly for serverless environments.

**Alternative Solution**: If we want truly serverless static file serving, configure Vercel to serve `apps/frontend/` directly via its CDN, separate from the Python app, and remove the static mounting code from `server.py` for production deployments.
