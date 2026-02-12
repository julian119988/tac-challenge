# Chore: Fix Vercel authentication blocking app access

## Metadata
adw_id: `Issue #60`
prompt: `I get this error {"error":"Not Found","message":"Path not found: /app"}
when entering https://tac-challenge-nethr36z5-julian-zambronis-projects.vercel.app/app`

## Chore Description

The Vercel deployment is blocking access to the application with an authentication page. When attempting to access `/app` or `/health` endpoints, users are redirected to a Vercel authentication page that says "Authenticating" and requires SSO login.

**Root Cause Analysis:**

The issue is NOT a path error or missing static files. The previous fix in Issue #58 correctly removed the `STATIC_FILES_DIR=/tmp/static` override. The actual problem is that Vercel's **Deployment Protection** feature is enabled on this deployment, which requires authentication before accessing any route.

**Evidence:**
1. The curl responses show Vercel's authentication page HTML instead of the actual app
2. The authentication page includes text: "Authentication Required" and "Vercel Authentication"
3. Both `/app` and `/health` endpoints return the same authentication page
4. The page contains authentication flow JavaScript and SSO redirects

**What is Deployment Protection:**
Vercel's Deployment Protection is a security feature that adds password or SSO authentication in front of preview deployments. This is commonly enabled for:
- Preview deployments (non-production branches)
- Security/privacy during development
- Team collaboration with access control

**Solutions:**

There are three approaches to fix this:

1. **Disable Deployment Protection** (Recommended for public apps like Focus Keeper)
   - Go to Vercel dashboard → Project Settings → Deployment Protection
   - Disable protection for preview deployments or set bypass rules
   - This makes the app publicly accessible

2. **Use Production Deployment**
   - Ensure the main branch is deployed to production (not preview)
   - Production deployments can have different protection rules
   - Update DNS/domain to point to production deployment

3. **Configure Bypass Rules**
   - Add IP allowlist for public access
   - Configure bypass tokens for automated access
   - Set specific paths to be publicly accessible

For Focus Keeper (a camera-based focus app), the app should be publicly accessible since it's a demo/showcase application. The recommended solution is to disable Deployment Protection or ensure the production deployment is used.

## Relevant Files

Use these files to understand the deployment:

- **vercel.json** - Vercel deployment configuration. Already correctly configured for routing after Issue #58 fix.

- **apps/adw_server/server.py** - FastAPI server that handles all routes including `/app` static files and `/health` endpoint. Server code is correct.

- **apps/adw_server/core/config.py** - Configuration management with static_files_dir defaulting to `apps/frontend`. Configuration is correct.

- **VERCEL_DEPLOYMENT.md** - Deployment documentation. Should be updated with guidance about Deployment Protection settings.

### New Files
None needed - this is a Vercel dashboard configuration change.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Document the Authentication Issue
- Confirm that Deployment Protection is enabled on the Vercel deployment
- Document the current protection settings (password, SSO, or IP-based)
- Verify which deployment type is affected (preview vs production)

### 2. Provide Instructions to Disable Deployment Protection
- Create clear step-by-step instructions for accessing Vercel dashboard settings
- Document how to navigate to: Project Settings → Deployment Protection
- Explain the options for disabling or configuring protection

### 3. Alternative: Ensure Production Deployment
- Check if a production deployment exists on the main branch
- Verify production deployment URL and protection settings
- Document how to access the production deployment

### 4. Update Vercel Configuration Documentation
- Add a new section in VERCEL_DEPLOYMENT.md about Deployment Protection
- Document when to enable/disable protection based on app type
- Add troubleshooting guidance for "Authentication Required" errors
- Include screenshots or detailed navigation steps

### 5. Verify Access After Changes
- Test that `/app` endpoint returns the HTML frontend (not authentication page)
- Test that `/health` endpoint returns JSON health status
- Verify the app loads correctly in a browser without authentication prompts
- Confirm camera access and all app features work

### 6. Update Issue Tracking
- Document the resolution in the issue #60
- Explain the difference between this and issue #58 (path error vs authentication)
- Provide the production or unprotected deployment URL

## Validation Commands

Execute these commands to validate the chore is complete:

**Note:** These commands will only work AFTER Deployment Protection is disabled or when run against a production deployment without protection.

- `curl -I https://your-vercel-deployment.vercel.app/app` - Should return `200 OK` and HTML content-type (not 302 redirect to authentication)
- `curl https://your-vercel-deployment.vercel.app/health` - Should return `{"status":"ok","service":"adw-webhook-server","environment":"production"}`
- Open `https://your-vercel-deployment.vercel.app/app` in browser - Should display Focus Keeper app without authentication prompt
- Verify camera permissions can be granted and app functions work

## Notes

**Key Distinction from Issue #58:**

- **Issue #58**: Was about static file path configuration (`STATIC_FILES_DIR=/tmp/static` being set incorrectly)
- **Issue #60**: Is about Vercel Deployment Protection blocking all access with authentication

**Current Status:**
- Issue #58 fix is correct and complete (removed `STATIC_FILES_DIR` override)
- Static files configuration now defaults to `apps/frontend` as intended
- The FastAPI server mounts static files correctly at `/app`
- The blocking issue is purely a Vercel dashboard security setting

**Why This Happens:**
Vercel enables Deployment Protection by default on some plans for preview deployments. This is a security feature to prevent unauthorized access during development. However, for public demo apps like Focus Keeper, this protection should be disabled or the app should be deployed to production without protection.

**Manual Steps Required:**

Since this is a Vercel dashboard configuration issue, the fix requires manual action in the Vercel dashboard. The steps are:

1. Log in to Vercel dashboard at https://vercel.com
2. Navigate to the tac-challenge project
3. Go to Settings → Deployment Protection
4. Choose one of:
   - Disable protection entirely for this project
   - Set protection to "Only Production" and use the production URL
   - Add your IP to the allowlist
   - Configure bypass tokens for public access

**Recommended Setting:**
For Focus Keeper (a public demo app), disable Deployment Protection or set it to "Only Production" and ensure preview deployments are accessible.

**Production vs Preview:**
- Preview deployments: Generated for every branch/commit (like `tac-challenge-nethr36z5-julian-zambronis-projects.vercel.app`)
- Production deployment: The main deployment, usually on a custom domain or the main Vercel URL
- Protection can be configured differently for each type

**Documentation Update:**
Add a section to VERCEL_DEPLOYMENT.md explaining:
- What Deployment Protection is
- How to configure it for public vs private apps
- Troubleshooting authentication errors
- Best practices for Focus Keeper specifically
