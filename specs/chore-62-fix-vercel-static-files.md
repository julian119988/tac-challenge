# Chore: Fix Vercel Static File Serving

## Metadata
adw_id: `8fd665e6`
prompt: `Issue #62: Vercel not loading files

There are a lot of files that are not loading on vercel
GET https://tac-challenge.vercel.app/styles.css 404 (Not Found)
GET https://tac-challenge.vercel.app/face-detection.js net::ERR_ABORTED 404 (Not Found)
GET https://tac-challenge.vercel.app/model-trainer.js net::ERR_ABORTED 404 (Not Found)
GET https://tac-challenge.vercel.app/eye-tracker.js net::ERR_ABORTED 404 (Not Found)
...`

## Chore Description

The Focus Keeper frontend application is not loading properly on Vercel because static files (CSS, JavaScript modules) are returning 404 errors. The issue is that the current `vercel.json` configuration routes ALL requests to the Python backend (`api/index.py`), but these static files need to be served directly by Vercel's CDN.

The root cause is that:
1. `vercel.json` has a catch-all route `"src": "/(.*)", "dest": "api/index.py"` that sends ALL requests to the Python backend
2. The frontend static files in `apps/frontend/` (like `styles.css`, `face-detection.js`, etc.) are not being served as static assets
3. When the browser requests these files, they get routed to the Python backend which doesn't know how to serve them, resulting in 404 errors

The solution requires:
1. Configuring `vercel.json` to serve `apps/frontend/` as a public static directory
2. Adding specific routes for static files that bypass the Python backend
3. Ensuring the Python backend only handles API routes (health checks, webhooks)
4. Testing that all static assets load correctly on Vercel

## Relevant Files

- **vercel.json** (root directory)
  - Vercel deployment configuration
  - Currently routes ALL requests to Python backend
  - Needs routes for static file serving and proper route ordering

- **apps/frontend/index.html**
  - Main HTML entry point for Focus Keeper app
  - References static assets like `styles.css`, `face-detection.js`, etc.
  - Needs to be served directly by Vercel

- **apps/frontend/*.js** (all JavaScript modules)
  - JavaScript modules: `face-detection.js`, `model-trainer.js`, `eye-tracker.js`, `app.js`, etc.
  - Currently returning 404 on Vercel
  - Need to be served as static files

- **apps/frontend/styles.css**
  - Main stylesheet for the application
  - Currently returning 404 on Vercel
  - Needs to be served as a static file

- **apps/frontend/config.js**
  - Configuration module
  - Needs to be served as a static file

- **apps/adw_server/server.py** (lines 408-428)
  - FastAPI server that currently handles static file serving in local development
  - In Vercel, static files should be served by CDN instead
  - May need adjustments to ensure proper routing

## Step by Step Tasks

### 1. Configure Vercel Static File Serving
- Add `public` directory configuration to `vercel.json` to mark `apps/frontend` as a source of static files
- Configure Vercel to copy or reference the frontend directory for static serving

### 2. Update Vercel Routes Configuration
- Reorder routes in `vercel.json` to prioritize static files before the Python backend
- Add specific routes for health check endpoints (`/health`, `/health/ready`)
- Add specific routes for webhook endpoints (`/`, `/webhooks/github` - POST only)
- Add a route to serve `/app` from the frontend's `index.html`
- Add catch-all route for static frontend assets (CSS, JS files)
- Ensure the Python backend route only catches remaining API routes
- Follow Vercel's route matching order: specific routes first, wildcards last

### 3. Test Static File Paths
- Verify that the frontend `index.html` references files with correct paths
- Ensure all JavaScript module imports use relative paths
- Check that `styles.css` link in HTML is correct
- Confirm video files and other assets in `apps/frontend/assets/` are accessible

### 4. Validate Local Serving Still Works
- Test that the FastAPI server still serves the frontend correctly in local development
- Ensure backward compatibility with the existing local setup
- Run the server locally and verify `/app` endpoint works

### 5. Test Vercel Deployment
- Deploy to Vercel (or test with existing deployment)
- Verify all static files load without 404 errors:
  - `GET /styles.css` → 200 OK
  - `GET /face-detection.js` → 200 OK
  - `GET /model-trainer.js` → 200 OK
  - `GET /eye-tracker.js` → 200 OK
  - `GET /app.js` → 200 OK
  - `GET /config.js` → 200 OK
  - All other `.js` modules in `apps/frontend/`
- Verify the Focus Keeper app loads and initializes properly
- Verify webhook endpoints still work (POST `/`, POST `/webhooks/github`)
- Verify health check endpoints still work (GET `/health`, GET `/health/ready`)

## Validation Commands

Execute these commands to validate the chore is complete:

- `ls -la apps/frontend/` - Verify all frontend files exist and are readable
- `curl https://tac-challenge.vercel.app/health` - Should return `{"status":"ok","service":"adw-webhook-server","environment":"production"}`
- `curl https://tac-challenge.vercel.app/styles.css` - Should return CSS content (not 404)
- `curl https://tac-challenge.vercel.app/face-detection.js` - Should return JavaScript content (not 404)
- `curl https://tac-challenge.vercel.app/app` - Should return HTML content (index.html)
- Access `https://tac-challenge.vercel.app/app` in browser - Should load Focus Keeper app without console errors
- Check browser console for any remaining 404 errors
- Verify camera initialization and face detection works on deployed app

## Notes

### Vercel Static File Serving Approaches

There are two main approaches to serve static files on Vercel:

1. **Using `public` directory** (Recommended for this case):
   - Files in a directory specified in `vercel.json` under `public` are served automatically
   - No need for custom routes for each file type
   - Vercel's CDN handles caching and optimization
   - Works with serverless functions in the same project

2. **Using route rewrites**:
   - Custom routes in `vercel.json` that map URL patterns to static files
   - More control over routing but more configuration
   - Can be combined with public directory approach

### Route Ordering in vercel.json

Vercel processes routes in order from top to bottom. The first matching route wins. Therefore:
- More specific routes must come BEFORE wildcard routes
- Static file routes should come BEFORE the Python backend catch-all
- Order matters significantly for preventing 404 errors

### Key Considerations

- Vercel's serverless environment has a read-only filesystem except for `/tmp`
- Static files should be served by Vercel's CDN, not the Python backend
- The Python backend (FastAPI) is only for webhooks and health checks in production
- In local development, FastAPI serves both backend API and frontend static files
- The `/app` route should serve the `index.html` from the frontend directory
- Root path `/` can redirect to `/app` for user-friendly access

### Previous Issues Fixed

- **Issue #56**: Initial Vercel deployment setup
- **Issue #58**: Fixed path configuration for static files directory
- **Issue #60**: Fixed Vercel Deployment Protection blocking app access
- **Issue #62** (Current): Fix static file serving so CSS and JS files load properly
