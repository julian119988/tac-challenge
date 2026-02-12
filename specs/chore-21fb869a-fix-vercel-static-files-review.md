# Chore: Fix Vercel Static File Serving (Review Feedback Implementation)

## Metadata
adw_id: `21fb869a`
prompt: `Issue #62: Vercel not loading files - Re-implementation addressing review feedback

Original issue: Files returning 404 on Vercel deployment
Review feedback identified: Critical path resolution issues, header source mismatches, overly aggressive caching, and missing CORS configuration

Critical issues to fix:
1. Path resolution uncertainty - routes use /apps/frontend/ destinations but Vercel may not resolve these correctly
2. Headers source mismatch - headers apply to /apps/frontend/(.*) but requests come to root paths like /styles.css
3. CORS header scope incorrect - applies to /api/(.*) but backend is at / and other routes
4. Cache control too aggressive for unversioned assets
5. No test deployment validation performed

Review recommends: Use a build step or public directory to properly serve static files, fix header paths to match request URLs, adjust cache controls for unversioned files`

## Chore Description

The previous implementation of the Vercel static file fix has critical issues that prevent proper static file serving. The main problems identified in code review are:

**Critical Issues:**
1. **Path resolution uncertainty**: Routes use destinations like `/apps/frontend/index.html` and `/apps/frontend/$1`, but Vercel's static file serving doesn't work this way. Vercel expects files in repository root or a `public` directory configured via build steps or explicit output directory configuration.

2. **Headers source mismatch**: The headers section uses source patterns like `/apps/frontend/(.*\\.css)` to match files, but actual request URLs will be `/styles.css`, not `/apps/frontend/styles.css`. Headers must match REQUEST URLs, not filesystem paths.

**Moderate Issues:**
3. **CORS header scope**: CORS headers apply to `/api/(.*)` but the Python backend is actually at `/` and other routes based on vercel.json routes configuration.

4. **Overly aggressive caching**: CSS/JS files have `max-age=31536000` (1 year) with `immutable`, which is only appropriate for versioned/hashed filenames. Current files are unversioned (`app.js`, not `app.abc123.js`), risking stale code in browsers.

**Minor Issues:**
5. **HTML cache too strict**: `max-age=0` means no caching at all, could use short cache like 60s for better performance.

6. **Validation script not tested**: Script exists but wasn't run against actual deployment to verify it works.

The solution requires:
1. **Use proper Vercel static file approach**: Copy files to `public/` directory at build time OR configure Vercel to recognize `apps/frontend/` as static source
2. **Fix header source patterns**: Match request URLs (e.g., `/styles.css`) not filesystem paths
3. **Adjust cache controls**: Use shorter caches for unversioned assets (1 hour instead of 1 year)
4. **Proper CORS configuration**: Only apply where actually needed
5. **Test the validation script**: Run against actual deployment

## Relevant Files

### Existing Files to Modify

- **vercel.json** (lines 9-99)
  - Main Vercel configuration file
  - Currently has incorrect path destinations and header sources
  - Needs route restructuring, header path fixes, and cache control adjustments
  - Critical: Fix destinations to not reference `/apps/frontend/` directly
  - Critical: Fix header sources to match request URLs

- **scripts/validate_vercel_routes.sh** (entire file)
  - Validation script for testing deployment routes
  - Needs to be run and potentially enhanced with error handling for curl failures
  - Should test actual deployment after changes

- **apps/frontend/index.html** (lines 7, 63-73)
  - References all the static assets with relative paths
  - May need path adjustments depending on chosen static file approach
  - Currently uses root-relative paths (e.g., `href="styles.css"`)

### Frontend Static Files (Reference)

All files in `apps/frontend/` that need to be served:
- `styles.css` - Main stylesheet
- `config.js`, `utils.js` - Utility modules
- `app.js` - Main application entry
- `face-detection.js`, `eye-tracker.js`, `dataset-manager.js` - Feature modules
- `model-trainer.js`, `gaze-predictor.js`, `heatmap-viz.js` - ML modules
- `ui-controller.js`, `video-player.js` - UI modules
- `assets/skeleton-attention.mp4` - Video asset
- `index.html` - HTML entry point

### New Files to Create

- **public/.gitkeep**
  - Marker for public directory if using build copy approach
  - Ensures directory exists in git

- **.vercelignore** (if needed)
  - Control what gets deployed to Vercel
  - May help with deployment size

- **package.json** (if using build step approach)
  - Define build command to copy files to public/
  - Scripts for pre-deployment setup

## Step by Step Tasks

### 1. Analyze Vercel Static File Serving Options
- Research Vercel's recommended approaches for serving static files in Python projects
- Determine if we should use: (A) build step to copy to `public/`, (B) direct serving from `apps/frontend/`, or (C) rewrites configuration
- Consider that Vercel Python projects can still serve static files from specific directories
- Check if `apps/frontend/` can be made a static directory without build steps (simplest approach)
- Document the chosen approach and rationale

### 2. Fix Critical Path Resolution Issues in vercel.json
- Update route destinations to use proper Vercel static file paths
- If using `public/` approach: Add build configuration to copy `apps/frontend/*` to `public/`
- If using direct serve approach: Configure routes to properly reference `apps/frontend/` as static source
- Remove incorrect path references like `/apps/frontend/$1` that Vercel can't resolve
- Ensure routes are ordered correctly: specific routes before wildcards
- Test that destinations resolve to actual servable files

### 3. Fix Critical Header Source Path Mismatches
- Update all header `source` patterns to match REQUEST URLs, not filesystem paths
- Change `/apps/frontend/(.*\\.css)` to `/(.*\\.css)` - matches requests to root
- Change `/apps/frontend/(.*\\.js)` to `/(.*\\.js)` - matches requests to root
- Change `/apps/frontend/(.*\\.html)` to `/(.*\\.html)` or `/app` specifically
- Update media file headers similarly: `/apps/frontend/(.*\\.(mp4|webm...))` to `/(.*\\.(mp4|webm...))`
- Verify each header source pattern matches the actual HTTP request path

### 4. Fix Moderate Cache Control Issues
- Adjust CSS/JS cache from `max-age=31536000, immutable` to `max-age=3600` (1 hour)
  - Reason: Files are unversioned, 1-year cache causes stale code issues
  - 1 hour provides good performance while allowing updates
- Adjust HTML cache from `max-age=0` to `max-age=60` (1 minute)
  - Reason: Still fresh but reduces server load
  - Still has `must-revalidate` for additional freshness guarantee
- Keep media files at `max-age=604800` (1 week) - these change rarely
- Add comments in spec explaining cache strategy (JSON doesn't support comments)

### 5. Fix CORS Configuration Scope
- Review which routes actually need CORS headers
- Python backend routes: `/`, `/health`, `/health/ready`, `/webhooks/github`
- Static files typically don't need CORS for same-origin requests
- Update CORS header source from `/api/(.*)` to match actual backend routes
- Consider if CORS is needed at all - check if frontend and backend are same origin
- Test cross-origin scenarios if CORS is required

### 6. Add Inline Documentation
- Since vercel.json doesn't support comments, create a comprehensive comment block in this spec
- Document route order importance
- Document header path matching logic
- Document cache control strategy
- Document why specific paths are chosen
- This spec serves as the documentation for vercel.json

### 7. Test with Validation Script
- Make validation script executable: `chmod +x scripts/validate_vercel_routes.sh`
- Run validation script against local server first: `./scripts/validate_vercel_routes.sh http://localhost:8000`
- Fix any issues found in local testing
- Deploy to Vercel test environment
- Run validation script against Vercel deployment: `./scripts/validate_vercel_routes.sh https://tac-challenge.vercel.app`
- Document all test results
- Fix any failures found during validation

### 8. Enhance Validation Script (Optional but Recommended)
- Add error handling for curl command failures
- Add timeout flags to curl commands to prevent hanging
- Add content-type checks in addition to status codes
- Add file size sanity checks (e.g., CSS file should be >100 bytes)
- Test that JavaScript files are actually JavaScript (basic syntax check)
- Add option to output detailed headers for debugging

### 9. Verify All Route Types Work
- Test health check endpoints: `GET /health`, `GET /health/ready`
- Test webhook endpoint: `POST /` with mock payload
- Test root redirect: `GET /` should redirect to `/app`
- Test app entry: `GET /app` should return HTML
- Test all static assets: CSS, JS modules, video files
- Test that 404s work correctly for non-existent paths
- Verify backend routes still work after changes

### 10. Document the Implementation
- Update this spec with final chosen approach
- Document any Vercel-specific quirks encountered
- Note any trade-offs made in the implementation
- Provide troubleshooting guide for future issues
- Document how to test locally vs production

## Validation Commands

Execute these commands to validate the chore is complete:

**Pre-deployment validation:**
```bash
# Verify frontend files exist and are readable
ls -la apps/frontend/*.{js,css,html}
ls -la apps/frontend/assets/*.mp4

# Verify vercel.json syntax is valid
cat vercel.json | python -m json.tool > /dev/null && echo "JSON valid"

# Test local server still works
# Start server in background, test, then kill
./scripts/start_webhook_server.sh &
sleep 5
curl -s http://localhost:8000/health | grep -q "ok" && echo "Local health check: PASS"
curl -s http://localhost:8000/app | grep -q "Focus Keeper" && echo "Local app endpoint: PASS"
pkill -f "uvicorn apps.adw_server.server:app"
```

**Post-deployment validation:**
```bash
# Make validation script executable
chmod +x scripts/validate_vercel_routes.sh

# Run full validation suite against Vercel deployment
./scripts/validate_vercel_routes.sh https://tac-challenge.vercel.app

# Manual verification of specific critical files
curl -I https://tac-challenge.vercel.app/styles.css | grep "200 OK"
curl -I https://tac-challenge.vercel.app/app.js | grep "200 OK"
curl -I https://tac-challenge.vercel.app/face-detection.js | grep "200 OK"

# Check cache-control headers are correct
curl -I https://tac-challenge.vercel.app/styles.css | grep -i "cache-control"
curl -I https://tac-challenge.vercel.app/app | grep -i "cache-control"

# Verify content types are correct
curl -I https://tac-challenge.vercel.app/styles.css | grep "content-type: text/css"
curl -I https://tac-challenge.vercel.app/app.js | grep "content-type.*javascript"

# Browser testing
# Open https://tac-challenge.vercel.app/app in browser
# Open browser console and verify:
# - No 404 errors for any static files
# - All JavaScript modules load successfully
# - Camera initialization works
# - Application functions normally
```

**Success criteria:**
- All curl commands return expected status codes (200 for existing files)
- Cache-Control headers match request URLs and have appropriate values
- No 404 errors in browser console when loading /app
- Application loads and functions normally on Vercel
- Validation script passes all tests
- Backend routes (health checks, webhooks) still work
- Static files serve with correct content types

## Notes

### Vercel Static File Serving in Python Projects

Vercel's Python runtime (@vercel/python) is designed primarily for serverless functions, but static files can still be served using these approaches:

**Option A: Public Directory (Simplest - Recommended)**
- Place files in `public/` directory at project root
- Vercel automatically serves files from `public/` without configuration
- Can use build step to copy `apps/frontend/*` to `public/` before deployment
- Routes in vercel.json can reference `/` paths which map to `public/`

**Option B: Direct Rewrites**
- Use rewrites/routes in vercel.json to map URLs to files
- Must specify complete paths including `apps/frontend/`
- Requires careful route ordering to prevent conflicts
- More complex but gives granular control

**Option C: Output Directory Configuration**
- Some frameworks support `outputDirectory` in vercel.json
- May not be fully supported for Python projects
- Worth investigating but likely not viable here

### Route Ordering Strategy

Vercel processes routes in order (first match wins), so order must be:
1. Health check routes (specific paths): `/health`, `/health/ready`
2. Root redirect (specific path): `/` with GET method
3. Webhook routes (specific paths with POST): `/`, `/webhooks/github`
4. App entry point (specific path): `/app`
5. Static file patterns (by extension): `/(.*\.(js|css|html|...))`
6. Fallback to backend (catch-all): `/(.*)`

### Cache Control Strategy

For **unversioned assets** (our case):
- **JavaScript/CSS**: `max-age=3600` (1 hour)
  - Provides caching benefit without long-term staleness
  - Users get updates within an hour of deployment
  - Balances performance vs freshness

- **HTML**: `max-age=60, must-revalidate` (1 minute)
  - Very fresh, users see updates quickly
  - `must-revalidate` forces check even if cached
  - Reduces server load vs max-age=0

- **Media (videos/images)**: `max-age=604800` (1 week)
  - These rarely change
  - Larger files benefit from longer cache
  - 1 week is reasonable compromise

For **versioned assets** (future consideration):
- If assets are hashed (e.g., `app.abc123.js`), can use `max-age=31536000, immutable`
- This requires build process to add content hashes to filenames
- Not implemented currently, but best practice for production

### Header Source Pattern Matching

**Critical Understanding**: Header `source` patterns match the REQUEST URL, not the filesystem path.

❌ **WRONG:**
```json
{
  "source": "/apps/frontend/(.*\\.css)",
  "headers": [{"key": "Cache-Control", "value": "..."}]
}
```
This looks for requests to `/apps/frontend/styles.css`, which never happens.

✅ **CORRECT:**
```json
{
  "source": "/(.*\\.css)",
  "headers": [{"key": "Cache-Control", "value": "..."}]
}
```
This matches requests to `/styles.css`, which is what browsers actually request.

### CORS Considerations

CORS (Cross-Origin Resource Sharing) headers are needed when:
- Frontend on domain A makes requests to backend on domain B
- Or when external sites need to access your API

In our deployment:
- Frontend served from: `https://tac-challenge.vercel.app/app`
- Backend routes at: `https://tac-challenge.vercel.app/` (POST), `/health`, etc.
- These are same-origin, CORS may not be needed for our own frontend

However, CORS may still be useful for:
- Testing from localhost during development
- Allowing GitHub webhooks (though webhooks are server-to-server)
- Future API access from other domains

Decision: Keep CORS for backend routes, but scope it correctly to actual backend paths.

### Vercel Deployment Protection

Previous issue #60 dealt with Vercel Deployment Protection. This is separate from static file serving:
- Deployment Protection is a Vercel feature that restricts access to preview deployments
- Production deployments are publicly accessible by default
- Not related to 404 errors on static files

### Testing Strategy

**Local testing first:**
1. Start local FastAPI server
2. Test all routes work locally
3. Verify file paths are correct
4. Use validation script against localhost

**Then Vercel testing:**
1. Deploy to Vercel (preview deployment is fine)
2. Run validation script against Vercel URL
3. Manual browser testing in console
4. Check Network tab for actual requests
5. Verify no 404s or CORS errors

**Common issues to watch for:**
- Case sensitivity: Linux/Vercel is case-sensitive, macOS isn't always
- Path separators: Use forward slashes `/` not backslashes
- Trailing slashes: Be consistent
- URL encoding: Special characters in filenames

### Review Feedback Summary

This implementation addresses all issues from review feedback:

✅ **Critical Issues Fixed:**
- Path resolution: Use proper Vercel static file approach
- Header sources: Match request URLs, not filesystem paths

✅ **Moderate Issues Fixed:**
- CORS scope: Apply only to actual backend routes
- Cache controls: Use reasonable values for unversioned assets
- Validation: Run script against actual deployment

✅ **Minor Issues Fixed:**
- HTML cache: Use short cache (60s) instead of none (0s)
- Documentation: This spec serves as comprehensive documentation

### Alternative Implementation Notes

If the chosen approach doesn't work, fallback options:
1. Try Vercel's `cleanUrls` and `trailingSlash` configuration options
2. Consider using Vercel's `outputDirectory` if supported
3. Could add a simple build script to organize files Vercel expects
4. Could use Vercel's `includeFiles` to specify what to deploy

### Related Issues History

- **Issue #56**: Initial Vercel deployment setup - First attempt at Vercel config
- **Issue #58**: Path error vercel - Fixed working directory paths
- **Issue #60**: Vercel Deployment Protection - Access restriction issue
- **Issue #62** (Current): Static files 404 - This implementation with review feedback
