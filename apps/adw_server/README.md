# ADW Automation Server

FastAPI server for GitHub webhook integration and ADW workflow automation.

## Structure

```
apps/adw_server/
├── core/                      # Core modules
│   ├── __init__.py           # Module exports
│   ├── config.py             # Server configuration
│   ├── handlers.py           # GitHub webhook handlers
│   └── adw_integration.py    # ADW workflow integration
├── server.py                 # Main FastAPI application
├── main.py                   # Entry point
└── .env.example              # Environment configuration template
```

## Quick Start

### 1. Set up environment

```bash
cd apps/adw_server
cp .env.example .env
# Edit .env and set GITHUB_WEBHOOK_SECRET and ANTHROPIC_API_KEY
```

### 2. Start the server

**From project root:**
```bash
./start_webhook_server.sh
```

**Or directly:**
```bash
# Using uv (recommended - handles dependencies automatically)
PYTHONPATH=. uv run --with fastapi --with "uvicorn[standard]" --with pydantic --with pydantic-settings --with python-dotenv uvicorn apps.server.server:app --host 0.0.0.0 --port 8000

# Using Python + pip
pip install -r requirements.txt
python apps/adw_server/main.py
```

### 3. Access the server

- **Health check:** http://localhost:8000/health
- **Camera app:** http://localhost:8000/app
- **GitHub webhooks:** http://localhost:8000/ (POST)

## Core Modules

### config.py

Server configuration management using Pydantic settings:
- Loads environment variables from `.env`
- Validates required settings
- Provides default values
- Environment-specific configuration

**Key settings:**
- `GITHUB_WEBHOOK_SECRET` - Required for webhook validation
- `ANTHROPIC_API_KEY` - Required for ADW workflows
- `SERVER_HOST` / `SERVER_PORT` - Server binding
- `ADW_WORKING_DIR` - Working directory for workflows
- `STATIC_FILES_DIR` - Frontend static files location

### handlers.py

GitHub webhook event processing:
- **Webhook signature validation** (HMAC-SHA256)
- **Event routing** for issues and pull requests
- **Label-based workflow mapping:**
  - `implement` / `bug` → Full workflow (plan + implement)
  - `feature` → Planning only
  - `chore` / `plan` → Planning only
- **Deduplication** to prevent duplicate workflows
- **GitHub comment posting** for status updates

### adw_integration.py

Interface between webhook server and ADW system:
- **`trigger_chore_workflow()`** - Run planning workflow
- **`trigger_implement_workflow()`** - Run implementation workflow
- **`trigger_chore_implement_workflow()`** - Run full workflow
- **Async execution** compatible with FastAPI
- **Output management** in `agents/{adw_id}/` directories

## Endpoints

### Health & Status

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (verifies ADW modules)

### GitHub Webhooks

- `POST /` - Primary webhook endpoint
- `POST /webhooks/github` - Alternative webhook endpoint

**Required headers:**
- `X-GitHub-Event` - Event type (issues, pull_request)
- `X-Hub-Signature-256` - Webhook signature

### Frontend

- `GET /app` - Serve camera app
- `GET /static/*` - Static file serving

## Webhook Setup

### 1. Configure GitHub Webhook

Go to repository **Settings → Webhooks → Add webhook**:

- **Payload URL:** `https://your-server.com/` or use ngrok for local: `https://abc123.ngrok.io/`
- **Content type:** `application/json`
- **Secret:** Same as `GITHUB_WEBHOOK_SECRET` in `.env`
- **Events:** Select "Issues" and "Pull requests"

### 2. Test the Integration

**Issue Workflow:**

Create a new issue with one of these labels:
- `implement` - Triggers full workflow
- `bug` - Triggers full workflow
- `feature` - Triggers planning only
- `chore` or `plan` - Triggers planning only

The webhook server will:
1. Validate the webhook signature
2. Post initial comment to issue
3. Trigger appropriate ADW workflow
4. Post completion comment with results

**Pull Request Review Workflow:**

When a Pull Request is created or updated that references an issue (using "Closes #N", "Fixes #N", or "Resolves #N" in the PR description), the webhook server will:
1. Extract issue references from the PR body
2. Post initial review comment to the linked issue(s)
3. Trigger the `/review` workflow to analyze code and run tests
4. Post review results to the linked issue(s) with:
   - Code review summary
   - Test results
   - Approval status
   - Link to PR
5. **Take automated actions based on review status:**
   - **APPROVED:** Automatically merge the PR (if enabled)
   - **CHANGES REQUESTED:** Automatically trigger re-implementation with review feedback (if enabled)
   - **NEEDS DISCUSSION:** Post results only, require manual intervention

**Note:** PRs without issue references will not trigger the review workflow. This ensures reviews are posted to the appropriate issue threads.

**Automated Post-Review Actions:**

The system can automatically handle review results:

- **Auto-Merge on Approval:**
  - When a review is APPROVED, the PR is automatically merged
  - Configurable via `AUTO_MERGE_ON_APPROVAL` environment variable
  - Uses configured merge method (`MERGE_METHOD`: squash, merge, or rebase)
  - Posts success/failure comment to the issue thread
  - Resets re-implementation attempt counter on successful merge

- **Auto-Reimplement on Changes:**
  - When a review has CHANGES REQUESTED, a new implementation cycle starts automatically
  - Configurable via `AUTO_REIMPLEMENT_ON_CHANGES` environment variable
  - Creates enhanced prompt with original issue + review feedback
  - Includes critical, moderate, and minor issues from review
  - Includes recommendations from review
  - Posts re-implementation status to issue thread

- **Loop Protection:**
  - Tracks re-implementation attempts per issue
  - Maximum attempts configurable via `MAX_REIMPLEMENT_ATTEMPTS` (default: 3)
  - After max attempts, requires manual intervention
  - Prevents infinite loops where agent repeatedly generates failing code
  - Counter resets when PR is successfully merged

**Configuration:**

Set these environment variables in `.env`:
```bash
# Enable/disable automatic merge on approved reviews
AUTO_MERGE_ON_APPROVAL=true

# Enable/disable automatic re-implementation on requested changes
AUTO_REIMPLEMENT_ON_CHANGES=true

# PR merge method (squash, merge, rebase)
MERGE_METHOD=squash

# Maximum re-implementation attempts per issue
MAX_REIMPLEMENT_ATTEMPTS=3
```

## Development

### Local Testing Without Webhooks

Test ADW integration directly:

```python
import asyncio
from core.adw_integration import trigger_chore_workflow

async def test():
    result = await trigger_chore_workflow(
        prompt="Test task",
        adw_id="test-001",
        model="sonnet"
    )
    print(f"Success: {result.success}")
    print(f"Plan: {result.plan_path}")

asyncio.run(test())
```

### Expose Local Server to Internet

For webhook testing with GitHub:

```bash
# Install ngrok: https://ngrok.com/
ngrok http 8000

# Use the ngrok URL as your GitHub webhook URL
# Example: https://abc123.ngrok.io/
```

### Hot Reload

The server runs with auto-reload in development mode:

```bash
uvicorn apps.server.server:app --reload
```

Changes to Python files will automatically restart the server.

## Environment Variables

See `.env.example` for complete list. Key variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_WEBHOOK_SECRET` | Yes | - | Webhook validation secret |
| `ANTHROPIC_API_KEY` | Yes | - | Claude API key for ADW |
| `SERVER_HOST` | No | 0.0.0.0 | Server host address |
| `SERVER_PORT` | No | 8000 | Server port |
| `ADW_WORKING_DIR` | No | Project root | Workflow working directory |
| `STATIC_FILES_DIR` | No | apps/frontend/dist | Frontend files location |
| `ENVIRONMENT` | No | development | Environment (dev/staging/prod) |
| `LOG_LEVEL` | No | INFO | Logging level |

## Troubleshooting

### Webhook signature validation fails

- Verify `GITHUB_WEBHOOK_SECRET` matches GitHub webhook configuration
- Check webhook payload is valid JSON
- Ensure `X-Hub-Signature-256` header is present

### ADW workflows not triggering

- Check issue has a supported label (`implement`, `bug`, `feature`, `chore`, `plan`)
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check logs for deduplication warnings (may be blocking duplicate triggers)
- Ensure Claude Code CLI is installed: `claude --version`

### Static files not serving

- Verify `STATIC_FILES_DIR` path is correct
- Check frontend build exists: `ls apps/frontend/dist/`
- Build frontend: `cd apps/frontend && npm run build`

### Module import errors

- Ensure running from project root with correct `PYTHONPATH`
- Check all dependencies installed: `pip install -r requirements.txt`
- Verify Python path includes project root

### Automatic merge failures

**Common causes:**
- **Merge conflicts:** PR branch conflicts with base branch
  - Solution: Resolve conflicts manually or update PR branch
- **Required checks not passing:** Branch protection rules require passing checks
  - Solution: Wait for checks to pass or update branch protection rules
- **GitHub permissions:** Token lacks `repo` write access
  - Solution: Verify `GITHUB_PAT` token has correct permissions
- **PR not in mergeable state:** Draft PR, closed PR, or already merged
  - Solution: Check PR status on GitHub

**Debug steps:**
1. Check server logs for merge error messages
2. Verify PR is mergeable on GitHub web interface
3. Test merge manually using `gh pr merge` command
4. Check GitHub token permissions: `gh auth status`

### Re-implementation loops

**Symptoms:**
- Same issue repeatedly triggers re-implementation
- Max attempts warning appears in issue comments
- Agent generates similar code that fails review repeatedly

**Solutions:**
- Review previous implementation attempts to identify pattern
- Check if requirements are clear and achievable
- Adjust `MAX_REIMPLEMENT_ATTEMPTS` if needed (default: 3)
- Close and re-open issue to reset counter
- Consider manual implementation for complex issues

**Prevention:**
- Write clear, specific issue descriptions
- Include acceptance criteria in issues
- Review auto-generated plans before implementation
- Use `NEEDS DISCUSSION` status for ambiguous cases

### Review workflow not posting results

**Common causes:**
- PR doesn't reference an issue (no "Closes #N" in description)
- GitHub token lacks permissions to post comments
- Rate limiting on GitHub API

**Solutions:**
- Add issue reference to PR description: "Closes #42"
- Check GitHub token permissions
- Review server logs for API errors
- Wait and retry if rate limited

## Logs

Server logs include:
- Webhook events received
- Workflow triggers and completions
- GitHub API calls (comments, label operations)
- Errors and warnings

**Log format:**
```
2026-02-09 17:03:19,908 - webhook_server - INFO - Received valid GitHub webhook: event=issues
2026-02-09 17:03:19,908 - apps.webhook_handlers - INFO - Handling issue event: #4 'Title' action=opened
2026-02-09 17:03:21,082 - apps.adw_integration - INFO - → trigger_chore_workflow called: adw_id=b175ca21
```

## Security

- **Webhook signatures** are validated using HMAC-SHA256
- **Secrets** are never logged or exposed in responses
- **CORS** can be restricted to specific domains in production
- **Rate limiting** is recommended for production deployments
- **HTTPS** should be used in production (configure reverse proxy)

## Production Deployment

### Recommended Setup

1. **Use HTTPS** - Configure reverse proxy (nginx, caddy)
2. **Set environment to production** - `ENVIRONMENT=production`
3. **Restrict CORS** - Set `CORS_ORIGINS` to specific domains
4. **Use strong secrets** - Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
5. **Run with workers** - `uvicorn apps.server.server:app --workers 4`
6. **Set up monitoring** - Health check endpoints for uptime monitoring
7. **Configure logging** - Structured JSON logs for analysis

### Example Production Command

```bash
uvicorn apps.server.server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level warning \
  --no-access-log \
  --proxy-headers
```

## Related Documentation

- **Project README:** `../../README.md` - Project overview and TAC framework
- **ADW Documentation:** `../../adws/README.md` - AI Developer Workflows
- **Webhook Spec:** `../../specs/chore-436b10a8-fastapi-webhook-server.md` - Implementation plan
- **Deduplication Fix:** `../../DEDUPLICATION_FIX.md` - Duplicate workflow prevention
