# Vercel Deployment Guide

This guide explains how to deploy the ADW webhook server to Vercel's serverless platform.

## Overview

The ADW webhook server can be deployed to Vercel as a serverless Python application. Vercel will automatically handle:
- Building the Python environment
- Installing dependencies from `requirements.txt`
- Routing HTTP requests to the FastAPI application
- Scaling based on demand

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. GitHub repository connected to Vercel
3. Required environment variables (see below)

## Deployment Steps

### 1. Connect Repository to Vercel

1. Log in to your Vercel dashboard
2. Click "Add New Project"
3. Import your GitHub repository
4. Vercel will auto-detect the `vercel.json` configuration

### 2. Configure Environment Variables

In the Vercel project settings, add the following environment variables:

#### Required Variables

- **GH_WB_SECRET**: Your GitHub webhook secret for validating webhook signatures
  - Generate a secure random string (e.g., `openssl rand -hex 32`)
  - Set this same value in your GitHub webhook configuration

- **ANTHROPIC_API_KEY**: Your Anthropic API key for Claude integration
  - Get your API key from https://console.anthropic.com/

#### Optional Variables (Most Set by vercel.json)

The following variables are automatically set by `vercel.json` for serverless deployment. You typically don't need to configure these manually:

- **ADW_WORKING_DIR**: Working directory for ADW operations
  - **Set by vercel.json**: `/tmp` (Vercel's only writable directory)
  - Note: Vercel's filesystem is ephemeral and only `/tmp` is writable
  - The application detects serverless environments and handles read-only filesystems automatically

- **STATIC_FILES_DIR**: Directory for static frontend files
  - **Set by vercel.json**: `/tmp/static`
  - Note: In serverless environments like Vercel, static files are typically served by the CDN, not the application
  - The application gracefully handles missing static directories in serverless environments

- **ENVIRONMENT**: Deployment environment
  - **Set by vercel.json**: `production`
  - Options: `development`, `production`

- **VERCEL**: Serverless environment indicator
  - **Set by Vercel platform**: `1` (string value, not boolean)
  - Used internally to detect Vercel serverless environment
  - Documented at: https://vercel.com/docs/concepts/projects/environment-variables#system-environment-variables

The following variables can be configured if needed:

- **SERVER_HOST**: Server host
  - Default: `0.0.0.0`

- **SERVER_PORT**: Server port
  - Default: `8000`

- **LOG_LEVEL**: Logging level
  - Default: `INFO`
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`

- **CORS_ENABLED**: Enable CORS
  - Default: `true`
  - Set to `false` if CORS is not needed

- **CORS_ORIGINS**: Allowed CORS origins (comma-separated)
  - Default: `["*"]`
  - Example: `https://yourapp.com,https://www.yourapp.com`

### 3. Deploy

1. Click "Deploy" in Vercel
2. Vercel will build and deploy your application
3. You'll receive a deployment URL (e.g., `https://your-app.vercel.app`)

### 4. Configure GitHub Webhook

1. Go to your GitHub repository settings
2. Navigate to "Webhooks" → "Add webhook"
3. Set the Payload URL to your Vercel deployment URL
   - For root endpoint: `https://your-app.vercel.app/`
   - Or use: `https://your-app.vercel.app/webhooks/github`
4. Set Content type to `application/json`
5. Set the Secret to match your `GH_WB_SECRET` environment variable
6. Select events:
   - Issues
   - Pull requests
7. Ensure the webhook is Active
8. Click "Add webhook"

## Testing the Deployment

### Health Check

Test the health endpoint to verify the server is running:

```bash
curl https://your-app.vercel.app/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "adw-webhook-server",
  "environment": "production"
}
```

### Readiness Check

Test the readiness endpoint to verify all services are ready:

```bash
curl https://your-app.vercel.app/health/ready
```

Expected response:
```json
{
  "status": "ready",
  "working_dir": "/tmp",
  "static_dir": "apps/camera_app/dist"
}
```

### Webhook Testing

1. Create a test issue in your GitHub repository
2. Add a label that triggers ADW (e.g., `feature`, `bug`, `chore`)
3. Check Vercel logs to see webhook processing
4. Verify ADW workflow execution

## Vercel-Specific Considerations

### Serverless Environment

The application automatically detects serverless environments and adjusts its behavior accordingly.

**Detection Criteria**:
- `VERCEL=1` environment variable (Vercel's documented convention)
- `AWS_LAMBDA_FUNCTION_NAME` environment variable (AWS Lambda)
- Working directory starts with `/var/task` (Vercel runtime path)
- Working directory starts with `/tmp` (common serverless pattern)

**Serverless Behavior**:
- Directory validation becomes lenient - creation failures are logged but don't fail startup
- Static files directory is optional (Vercel serves static files via CDN)
- Only `/tmp` is writable - all temporary files must go there
- Configuration loading logs environment detection for debugging

**Environment Characteristics**:
- **Ephemeral filesystem**: Files written to `/tmp` are temporary and may be deleted between invocations
- **Read-only filesystem**: Everything except `/tmp` is read-only
- **Execution time limit**: Vercel has a maximum execution time (10 seconds for Hobby, 60 seconds for Pro)
- **Cold starts**: First request after inactivity may be slower

### Static Files

The camera app static files are served from the `apps/camera_app/dist` directory. In Vercel's environment:
- Static files are included in the deployment
- The `/app` route serves the React application
- The `/static` route serves legacy static files

### Logging

Vercel captures all stdout/stderr output:
- View logs in the Vercel dashboard under "Logs"
- Real-time logs are available during deployment
- Historical logs are retained based on your Vercel plan

### Limitations

1. **Long-running processes**: ADW workflows that take longer than Vercel's timeout will fail
2. **File persistence**: Generated files (specs, patches, etc.) are not persisted between requests
3. **Git operations**: Git commands work but changes are not persisted to the repository from Vercel

For long-running ADW workflows, consider:
- Using Vercel Pro for longer timeouts
- Implementing async processing with a queue system
- Hosting on a traditional server (e.g., Railway, Render, AWS)

## Troubleshooting

### Configuration Validation Errors

If you encounter `ValidationError` during deployment:

**Symptom**: Error mentions "could not be created" or "does not exist"
**Cause**: The application is trying to create directories on a read-only filesystem
**Solution**:
- ✓ **Fixed in Issue #56 Review**: Configuration validators now automatically detect serverless environments
- Ensure `ADW_WORKING_DIR` points to `/tmp` (set in `vercel.json`)
- Ensure `STATIC_FILES_DIR` points to `/tmp/static` or another `/tmp` subdirectory
- Check Vercel logs for detailed error messages showing which paths are failing

**How it works**:
- The application detects serverless environments via:
  1. `VERCEL=1` environment variable (automatically set by Vercel)
  2. Working directory paths starting with `/var/task` or `/tmp`
  3. Presence of `AWS_LAMBDA_FUNCTION_NAME` (for AWS Lambda)
- In serverless mode, directory creation failures are logged but don't fail the deployment
- Static files are optional in serverless environments (served separately by CDN)

### Import Errors (FIXED in Issue #56)

If you see import errors in Vercel logs:
- ✓ **Fixed**: Updated `api/index.py` to use centralized import path setup
- ✓ **Fixed**: Created `core/serverless_utils.py` for consistent path configuration
- ✓ **Fixed**: Modified `config.py` validators to handle serverless environments
- ✓ **Fixed**: Set required environment variables in `vercel.json` (`ADW_WORKING_DIR`, `STATIC_FILES_DIR`)
- Verify all dependencies are in `requirements.txt`
- Ensure the project structure matches the import paths

**Technical Details of Fixes:**
- `api/index.py`: Uses `setup_import_paths()` from `serverless_utils` for consistent path configuration
- `core/serverless_utils.py`: Centralizes serverless detection and path setup logic
- `config.py`: Validators use `is_serverless_environment()` for consistent detection
- `config.py`: Added comprehensive logging for debugging configuration issues
- `vercel.json`: Sets environment variables for serverless-specific paths (`/tmp` directory)

### Webhook Signature Validation Fails

If webhooks are rejected with 401 errors:
- Verify `GH_WB_SECRET` matches in both Vercel and GitHub
- Check that the secret doesn't have extra whitespace
- Ensure the webhook is sending the `X-Hub-Signature-256` header

### ADW Workflows Not Triggering

If webhooks are received but ADW doesn't run:
- Check Vercel logs for errors
- Verify `ANTHROPIC_API_KEY` is set correctly
- Ensure the issue/PR has appropriate labels
- Check that ADW modules are accessible (see readiness check)

### Timeout Errors

If requests time out:
- ADW workflows may be too long for Vercel's timeout
- Consider upgrading to Vercel Pro for longer timeouts
- Or use a traditional server for long-running workflows

## Monitoring

### Vercel Dashboard

Monitor your deployment in the Vercel dashboard:
- **Deployments**: View deployment history and status
- **Logs**: Real-time and historical logs
- **Analytics**: Request counts and performance metrics (Pro plan)

### GitHub Webhook Deliveries

Monitor webhook deliveries in GitHub:
1. Go to repository Settings → Webhooks
2. Click on your webhook
3. View "Recent Deliveries" to see requests and responses
4. Click individual deliveries to see full request/response details

## Custom Domain (Optional)

To use a custom domain:
1. Go to Vercel project settings
2. Navigate to "Domains"
3. Add your custom domain
4. Update DNS records as instructed
5. Update GitHub webhook URL to use custom domain

## Updating the Deployment

Vercel automatically deploys when you push to your repository:
1. Make changes locally
2. Commit and push to your GitHub repository
3. Vercel detects the push and starts a new deployment
4. Monitor deployment progress in Vercel dashboard

## Rolling Back

If a deployment has issues:
1. Go to Vercel dashboard → Deployments
2. Find a previous working deployment
3. Click the three dots → "Promote to Production"
4. The previous deployment becomes active immediately

## Support

- Vercel Documentation: https://vercel.com/docs
- FastAPI Documentation: https://fastapi.tiangolo.com/
- GitHub Webhooks: https://docs.github.com/en/webhooks

## Next Steps

After successful deployment:
1. Test webhook integration with a sample issue/PR
2. Monitor logs for any errors
3. Set up monitoring/alerts (if using Vercel Pro)
4. Document any custom configuration for your team
