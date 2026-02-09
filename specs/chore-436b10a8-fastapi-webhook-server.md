# Chore: Create FastAPI Webhook Server

## Metadata
adw_id: `436b10a8`
prompt: `Create a FastAPI webhook server that listens for GitHub webhooks and triggers ADW workflows. Include endpoints for webhook handling, health checks, and serving the anti-procrastination camera app frontend.`

## Chore Description
Build a production-ready FastAPI server that acts as the central integration point for the application. The server will:

1. **GitHub Webhook Integration**: Receive and validate GitHub webhook events (issues, pull requests) and trigger appropriate ADW workflows based on event type and labels
2. **Health Monitoring**: Provide health check endpoints for monitoring server status
3. **Frontend Serving**: Serve the anti-procrastination camera app's static frontend files (HTML, CSS, JavaScript)
4. **ADW Workflow Triggering**: Interface with the existing ADW modules to programmatically trigger workflows like `/chore`, `/implement`, etc.

This server bridges the gap between external events (GitHub webhooks) and internal automation (ADW workflows), while also hosting the camera application's user interface.

## Relevant Files
Use these files to complete the chore:

- `README.md` - Project overview explaining the TAC framework and anti-procrastination app
- `adws/README.md` - ADW documentation explaining workflow execution patterns
- `adws/adw_modules/agent.py` - Core agent execution module that the server will use to trigger workflows
- `adws/adw_modules/data_types.py` - Type definitions for ADW data structures
- `adws/adw_modules/workflow_ops.py` - Workflow orchestration utilities (if available)
- `adws/adw_modules/github.py` - GitHub integration utilities (if available)
- `adws/adw_slash_command.py` - Reference for how to execute slash commands programmatically
- `adws/adw_chore_implement.py` - Reference for workflow composition patterns
- `apps/main.py` - Existing Python application structure

### New Files
- `apps/webhook_server.py` - Main FastAPI webhook server implementation
- `apps/server_config.py` - Server configuration management (environment variables, settings)
- `apps/webhook_handlers.py` - GitHub webhook event handlers and validation logic
- `apps/adw_integration.py` - Integration layer between server and ADW workflows
- `apps/static/index.html` - Anti-procrastination camera app frontend
- `apps/static/app.js` - Camera app JavaScript logic
- `apps/static/styles.css` - Camera app styling
- `requirements.txt` or `pyproject.toml` - Python dependencies including FastAPI, uvicorn, etc.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Analyze ADW Integration Points
- Review `adws/adw_modules/agent.py` to understand how to programmatically execute agents
- Review `adws/adw_slash_command.py` to see command execution patterns
- Review `adws/adw_chore_implement.py` to understand workflow composition
- Identify the correct way to trigger ADW workflows from the webhook server
- Understand output directory structure (`agents/{adw_id}/...`)

### 2. Create Server Configuration Module
- Create `apps/server_config.py` with Pydantic settings management
- Define configuration for:
  - Server host/port
  - GitHub webhook secret for validation
  - ADW execution settings (models, working directory)
  - Static file directory path
  - CORS settings if needed
- Use environment variables with sensible defaults
- Add validation for required secrets

### 3. Create ADW Integration Layer
- Create `apps/adw_integration.py` to interface with ADW modules
- Implement functions to trigger different workflows:
  - `trigger_chore_workflow(prompt: str, adw_id: str)` - Plan a chore
  - `trigger_implement_workflow(spec_path: str, adw_id: str)` - Implement a plan
  - `trigger_chore_implement_workflow(prompt: str, adw_id: str)` - Full workflow
- Handle async execution of workflows (FastAPI is async-native)
- Return workflow status and output paths
- Import and use `AgentPromptRequest`, `AgentTemplateRequest` from `adw_modules.agent`

### 4. Create Webhook Handler Module
- Create `apps/webhook_handlers.py` for GitHub webhook logic
- Implement GitHub webhook signature validation using HMAC-SHA256
- Create Pydantic models for GitHub webhook payloads (issues, pull requests)
- Implement event routing logic:
  - Issue events with label matching (e.g., `bug`, `feature`, `chore`)
  - Pull request events (opened, synchronize)
  - Other relevant events
- Map GitHub events to ADW workflows (e.g., `feature` label → `/chore` workflow)
- Generate unique ADW IDs for each webhook trigger
- Add comprehensive logging for debugging

### 5. Create Main FastAPI Server
- Create `apps/webhook_server.py` as the main server file
- Initialize FastAPI app with proper configuration
- Implement endpoints:
  - `GET /` - Redirect to `/app` or serve basic info
  - `GET /health` - Health check endpoint returning server status
  - `GET /health/ready` - Readiness check (verify ADW modules accessible)
  - `POST /webhooks/github` - GitHub webhook receiver endpoint
  - `GET /app` or `GET /app/` - Serve the camera app frontend (redirect to static)
- Add CORS middleware if needed for frontend
- Add request logging middleware
- Configure static file serving for `/static` path
- Add error handlers for common exceptions
- Include startup event to verify ADW modules are available

### 6. Create Anti-Procrastination Camera App Frontend
- Create `apps/static/index.html` with structure for camera app:
  - Video element for camera feed
  - Canvas for processing (if needed)
  - UI elements for status and controls
  - Placeholder for attention-grabbing video
- Create `apps/static/app.js` with camera functionality:
  - Request camera permissions
  - Access device camera via getUserMedia API
  - Placeholder for gaze detection logic (can use MediaPipe or similar)
  - Distraction detection triggers
  - Video playback control
- Create `apps/static/styles.css` for clean, minimal styling:
  - Responsive layout
  - Camera feed display
  - Status indicators
  - Control buttons
- Keep frontend simple and functional, focusing on core features

### 7. Add Dependency Management
- Create `requirements.txt` with dependencies:
  - `fastapi` - Web framework
  - `uvicorn[standard]` - ASGI server
  - `pydantic` - Data validation
  - `pydantic-settings` - Settings management
  - `python-dotenv` - Environment variable loading
  - `httpx` - Async HTTP client (for GitHub API if needed)
  - Any existing dependencies from ADW modules
- Alternatively, use `pyproject.toml` if project uses modern Python packaging

### 8. Add Comprehensive Documentation
- Add detailed docstrings to all modules and functions
- Include usage examples in server module
- Document webhook payload expectations
- Document environment variables needed
- Add inline comments for complex logic
- Follow Google or NumPy docstring style

### 9. Create Example Environment File
- Create `.env.example` showing required configuration:
  - `GITHUB_WEBHOOK_SECRET=your_secret_here`
  - `SERVER_HOST=0.0.0.0`
  - `SERVER_PORT=8000`
  - `ADW_WORKING_DIR=/path/to/project`
  - Other relevant settings
- Add instructions in docstring or comments

### 10. Validate Implementation
- Test server imports without errors
- Test server starts successfully
- Test health endpoints return expected responses
- Test webhook endpoint with mock GitHub payload
- Test static file serving for camera app
- Verify ADW integration can trigger workflows
- Test webhook signature validation
- Ensure proper error handling and logging

## Validation Commands
Execute these commands to validate the chore is complete:

- `python -m py_compile apps/webhook_server.py apps/server_config.py apps/webhook_handlers.py apps/adw_integration.py` - Verify Python syntax
- `python -c "from apps import webhook_server, server_config, webhook_handlers, adw_integration; print('All modules import successfully')"` - Test imports
- `python apps/webhook_server.py` - Start the server (should run without errors, can stop with Ctrl+C)
- `curl http://localhost:8000/health` - Test health endpoint (in separate terminal while server running)
- `curl http://localhost:8000/health/ready` - Test readiness endpoint
- `curl http://localhost:8000/app` - Test frontend serving
- `curl -X POST http://localhost:8000/webhooks/github -H "Content-Type: application/json" -d '{"action":"opened","issue":{"number":1}}'` - Test webhook endpoint (expect validation failure without signature)
- `ls apps/static/` - Verify static files exist (index.html, app.js, styles.css)

## Notes

### GitHub Webhook Setup
To connect GitHub to this server:
1. Go to repository Settings → Webhooks → Add webhook
2. Set Payload URL to: `https://your-server.com/webhooks/github`
3. Set Content type to: `application/json`
4. Set Secret to match `GITHUB_WEBHOOK_SECRET` env var
5. Select individual events: Issues, Pull requests
6. Save webhook

### ADW Workflow Mapping Strategy
Suggested label-to-workflow mapping:
- `bug` label → Trigger `/chore` with issue description, then `/implement` the plan
- `feature` label → Trigger `/chore` with issue description, then await manual approval before `/implement`
- `chore` label → Trigger `/chore` only for planning
- Pull request events → Trigger `/review` workflow (if available)

### Security Considerations
- Always validate GitHub webhook signatures using HMAC-SHA256
- Never expose GitHub webhook secret in logs or responses
- Rate limit webhook endpoint if needed
- Validate payload structure before processing
- Use HTTPS in production

### Production Deployment
- Use a production ASGI server like `uvicorn` with multiple workers
- Set up reverse proxy (nginx, caddy) for HTTPS
- Configure proper logging (structured JSON logs)
- Set up monitoring and alerting
- Use environment-specific configuration
- Consider containerization (Docker)

### Camera App Enhancement Opportunities
The initial camera app frontend will be minimal. Future enhancements could include:
- Integration with ML models for gaze detection (MediaPipe, TensorFlow.js)
- Customizable distraction detection sensitivity
- Multiple attention-grabbing video options
- Session tracking and productivity metrics
- Local storage for user preferences
