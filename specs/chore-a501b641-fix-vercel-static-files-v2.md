# Chore: Fix Vercel Static File Serving (V2 - Review Feedback)

## Metadata
adw_id: `a501b641`
prompt: `Vercel not loading files - Re-implement with review feedback addressing critical path mismatch, missing CORS headers, root path ambiguity, and other issues identified in code review`

## Chore Description

This is a re-implementation of issue #62 addressing critical review feedback. The Focus Keeper frontend application fails to load on Vercel because static files (CSS, JavaScript modules) return 404 errors. The previous implementation had several issues:

### Critical Issues to Fix:
1. **Static file path mismatch**: The route regex captures `styles.css` from request `/styles.css` and routes to `/apps/frontend/styles.css`, but Vercel may not resolve this correctly. Need to properly configure static file serving.
2. **Root path ambiguity**: No GET handler for `/` to redirect users to `/app`. Users visiting root URL hit Python backend.
3. **Missing CORS headers**: If frontend makes API calls to Python backend, CORS headers may be needed.

### Moderate Issues to Address:
1. **No cache control headers**: Static assets should have cache-control headers for performance.
2. **Regex complexity**: Static file regex needs clarification with comments.
3. **Missing validation**: Need automated validation for routes.

### Root Causes:
- Current `vercel.json` uses route rewrites with regex that may not properly resolve file paths
- No public directory configured for Vercel's CDN to serve static files directly
- HTML references files with root-relative paths (`href="styles.css"`) but Vercel routing doesn't map them correctly
- No root path (`/`) handler for GET requests
- Missing cache and CORS configuration for production optimization

### Solution Approach:
1. **Use Vercel's `public` directory configuration** instead of just route rewrites
2. **Add explicit static file routes** with proper ordering (specific before wildcard)
3. **Configure root path redirect** from `/` to `/app`
4. **Add CORS headers** for API routes
5. **Add cache-control headers** for static assets
6. **Document and validate** all route configurations
7. **Ensure backward compatibility** with local development setup

## Relevant Files

### Existing Files to Modify:

- **vercel.json** (root directory)
  - Primary configuration file for Vercel deployment
  - Needs proper static file configuration using `public` or `outputDirectory`
  - Needs route reordering: specific routes first, wildcards last
  - Needs CORS headers for API routes
  - Needs cache-control headers for static assets
  - Needs root path redirect handler

- **apps/frontend/index.html** (lines 7, 63-73)
  - References static assets with root-relative paths
  - May need to verify path consistency
  - Currently uses: `href="styles.css"`, `src="config.js"`, etc.

- **apps/adw_server/server.py**
  - FastAPI server that handles local development static file serving
  - May need CORS middleware for API routes if not already present
  - Should not need changes if CORS is configured in vercel.json

### New Files:

- **specs/chore-a501b641-fix-vercel-static-files-v2.md** (this file)
  - Comprehensive specification with review feedback addressed
  - Documents all issues and solutions
  - Includes validation steps

- **public/.gitkeep** (if using public directory approach)
  - Marker file if we create a public directory
  - Only needed if we copy/symlink frontend files to public/

## Step by Step Tasks

### 1. Analyze Vercel Static File Serving Options
- Research Vercel documentation for static file serving best practices
- Determine if we should use `public` directory, `outputDirectory`, or route rewrites
- Identify the correct approach for serving files from `apps/frontend/` directory
- Document the chosen approach and rationale

### 2. Update vercel.json with Proper Static File Configuration
- Add configuration to serve `apps/frontend/` as static files source
- Configure proper route ordering with comments explaining each route's purpose
- Add specific routes in this order:
  1. Health check routes (`/health`, `/health/ready`) → Python backend
  2. Root path GET redirect (`/` GET) → redirect to `/app` or serve index.html
  3. App entry point (`/app`) → `apps/frontend/index.html`
  4. Static asset route with regex for all file extensions → `apps/frontend/$1`
  5. Webhook routes (`/`, `/webhooks/github` POST only) → Python backend
  6. Catch-all for remaining API routes → Python backend
- Add headers configuration:
  - CORS headers for API routes (if needed)
  - Cache-control headers for static assets (CSS, JS, images, videos)
- Add clear comments explaining regex patterns and route matching logic
- Ensure the static file regex properly captures and routes files

### 3. Configure Headers for Production Optimization
- Add `headers` section to vercel.json for static assets:
  - Cache-Control for CSS/JS files (e.g., `public, max-age=31536000, immutable` for versioned assets)
  - Cache-Control for HTML files (e.g., `public, max-age=0, must-revalidate`)
  - Cache-Control for videos/images (e.g., `public, max-age=604800`)
- Add CORS headers for API routes if frontend makes cross-origin requests:
  - Access-Control-Allow-Origin
  - Access-Control-Allow-Methods
  - Access-Control-Allow-Headers
- Document why each header configuration is needed

### 4. Add Root Path Redirect Handler
- Configure GET `/` to redirect to `/app` for user-friendly access
- Ensure POST `/` still routes to webhook handler
- Test that users visiting root URL are redirected to the application
- Document the redirect behavior

### 5. Verify File Path References
- Review `apps/frontend/index.html` to confirm all asset references are correct:
  - CSS: `href="styles.css"`
  - JS modules: `src="config.js"`, `src="app.js"`, etc.
  - Assets: any references to `assets/skeleton-attention.mp4`
- Ensure all paths are consistent with Vercel routing configuration
- Confirm no hardcoded absolute URLs that would break in production

### 6. Test Local Development Setup
- Start FastAPI server locally: `./scripts/start_webhook_server.sh`
- Verify `/app` endpoint serves frontend correctly
- Verify all static files load without errors
- Ensure backward compatibility is maintained
- Check that local development workflow is not broken

### 7. Create Validation Script
- Write a shell script to validate Vercel deployment routes
- Script should test:
  - GET `/health` → 200 with JSON response
  - GET `/health/ready` → 200 with JSON response
  - GET `/` → 301/302 redirect to `/app` or serves HTML
  - GET `/app` → 200 with HTML content
  - GET `/styles.css` → 200 with CSS content
  - GET `/face-detection.js` → 200 with JavaScript content
  - GET `/app.js` → 200 with JavaScript content
  - GET `/assets/skeleton-attention.mp4` → 200 with video content
  - GET all other `.js` modules → 200
- Script should check response headers for proper cache-control
- Save as `scripts/validate_vercel_routes.sh`

### 8. Test Vercel Deployment
- Deploy to Vercel using `vercel deploy` or verify existing deployment
- Run validation script against deployed URL: `./scripts/validate_vercel_routes.sh https://tac-challenge.vercel.app`
- Manually test in browser:
  - Visit `https://tac-challenge.vercel.app/` → should redirect to `/app`
  - Visit `https://tac-challenge.vercel.app/app` → should load Focus Keeper
  - Open browser console → verify no 404 errors
  - Check Network tab → verify all static files return 200
  - Verify cache-control headers are present on static assets
- Test Focus Keeper functionality:
  - Camera initialization
  - Face detection
  - Video playback (if applicable)
- Test API endpoints:
  - POST webhook (if testable)
  - Health checks

### 9. Document Changes and Rationale
- Update this spec file with final implementation details
- Document what changed from previous implementation
- Explain why each change addresses specific review feedback
- Include before/after comparison of vercel.json routes
- Document any trade-offs or limitations

### 10. Validate All Review Feedback Addressed
- **Critical - Static file path mismatch**: ✓ Fixed with proper Vercel configuration
- **Critical - Root path ambiguity**: ✓ Added GET `/` redirect handler
- **Critical - Missing CORS headers**: ✓ Added CORS configuration if needed
- **Moderate - No cache control headers**: ✓ Added cache-control for static assets
- **Moderate - Regex complexity**: ✓ Added comments explaining regex patterns
- **Moderate - Missing validation**: ✓ Created validation script
- Confirm all files load correctly on Vercel
- Confirm no 404 errors in browser console
- Confirm proper headers are present

## Validation Commands

Execute these commands to validate the chore is complete:

### Local Development Validation:
```bash
# Start local server
./scripts/start_webhook_server.sh &
SERVER_PID=$!
sleep 5

# Test local endpoints
curl -s http://localhost:8000/health | jq .
curl -s -I http://localhost:8000/app | grep "200 OK"
curl -s http://localhost:8000/styles.css | head -5

# Kill server
kill $SERVER_PID
```

### Vercel Deployment Validation:
```bash
# Run validation script (to be created)
./scripts/validate_vercel_routes.sh https://tac-challenge.vercel.app

# Manual checks
curl -s https://tac-challenge.vercel.app/health | jq .
curl -s -I https://tac-challenge.vercel.app/styles.css | grep "200 OK"
curl -s -I https://tac-challenge.vercel.app/styles.css | grep -i "cache-control"
curl -s -I https://tac-challenge.vercel.app/face-detection.js | grep "200 OK"
curl -s -I https://tac-challenge.vercel.app/app | grep "200 OK"
curl -s -IL https://tac-challenge.vercel.app/ | grep -E "(301|302|200)"
```

### Browser Validation:
1. Open `https://tac-challenge.vercel.app/` in browser
2. Verify redirect to `/app` or direct load of application
3. Open Developer Console (F12)
4. Check Console tab for errors → should have no 404s
5. Check Network tab → verify all resources return 200
6. Check Network tab → verify cache-control headers on static files
7. Test Focus Keeper functionality (camera, face detection)

### File Structure Validation:
```bash
# Verify all frontend files exist
ls -la apps/frontend/*.js apps/frontend/*.css apps/frontend/*.html
ls -la apps/frontend/assets/

# Verify vercel.json is valid JSON
cat vercel.json | jq . > /dev/null && echo "✓ Valid JSON"
```

## Notes

### Vercel Static File Serving Best Practices

According to Vercel documentation, there are three main approaches:

1. **Public Directory** (Recommended for simple cases):
   - Files in `/public` are automatically served at root
   - No custom routes needed
   - Requires copying/moving files or using build step

2. **Output Directory** (Framework-specific):
   - Used by frameworks like Next.js, not applicable here
   - Not suitable for our vanilla JS app

3. **Route Rewrites** (Most flexible for our case):
   - Use regex routes to map URL patterns to file locations
   - Can serve files from any directory structure
   - Requires careful route ordering
   - **We'll use this approach** since our frontend is in `apps/frontend/`, not `/public`

### Critical: Route Ordering in vercel.json

Vercel processes routes **in order from top to bottom**. First match wins.

**Correct Order:**
1. Specific exact path routes (health checks, specific endpoints)
2. Redirect routes
3. Static file pattern routes with regex
4. API/backend routes (POST only, specific paths)
5. Catch-all wildcard routes (should be last or very specific)

**Incorrect Order (causes 404s):**
❌ Catch-all route first → matches everything, static files never reached
❌ Wildcard before specific routes → wrong handler gets requests

### Headers Configuration

**Cache-Control Strategy:**
- **HTML files**: `public, max-age=0, must-revalidate` (always check for updates)
- **CSS/JS files**: `public, max-age=31536000, immutable` (long cache, use versioning/hashing)
- **Video/Images**: `public, max-age=604800` (1 week cache)
- **API responses**: `no-cache, no-store, must-revalidate` (never cache)

**CORS Configuration:**
- Only needed if frontend makes API calls to backend from different origin
- In our case, frontend and backend are same origin on Vercel
- May still add for local development or future cross-origin scenarios
- Consider: `Access-Control-Allow-Origin: *` for public API or specific origins

### Vercel Limitations

- Serverless functions have read-only filesystem except `/tmp`
- Static files should be served by CDN, not Python backend
- Cold starts on serverless functions can add latency
- Response size limits apply to serverless functions

### Previous Implementation Issues (from Review)

**What was wrong:**
1. Route at vercel.json:34 used `/apps/frontend/$1` but Vercel couldn't resolve this path correctly
2. Browser requests `/styles.css` → regex captures `styles.css` → routes to `/apps/frontend/styles.css` → Vercel can't find file
3. No configuration telling Vercel where static files actually live
4. No root path GET handler, users visiting `/` hit Python backend
5. No caching or CORS headers for production

**How we're fixing it:**
1. Use proper Vercel route configuration with correct path resolution
2. Add explicit static file routes with correct destination paths
3. Configure headers for caching and CORS
4. Add root path redirect handler
5. Document and validate all routes thoroughly

### Testing Strategy

**Three-level validation:**
1. **Static validation**: Check vercel.json syntax, file existence
2. **Local validation**: Test routes on local development server
3. **Production validation**: Test routes on deployed Vercel environment

**Automated validation script should test:**
- All static file routes return 200
- All API routes return expected responses
- Headers are present and correct
- No 404s for any expected resources
- Redirects work correctly

### Backward Compatibility

**Must ensure:**
- Local development with FastAPI still works
- `./scripts/start_webhook_server.sh` still serves frontend
- No breaking changes to development workflow
- Python backend routes unchanged (health, webhooks)

### Additional Context

- **Previous fixes**: Issues #56, #58, #60 addressed deployment setup and path configuration
- **Current issue**: Issue #62 requires proper static file serving configuration
- **Review feedback**: This implementation addresses all critical, moderate, and minor issues from code review
- **Focus**: Getting static files to load correctly on Vercel while maintaining local development compatibility
