"""FastAPI ADW automation server for GitHub webhook integration.

This server provides ADW (AI Developer Workflows) automation through:
1. GitHub webhook endpoints for automated ADW workflow triggers
2. Health check endpoints for monitoring
3. Static file serving for the camera app frontend

The server is an automation tool that bridges external events (GitHub webhooks)
and ADW workflows for automated development tasks.

Usage:
    # Run with default settings (requires GITHUB_WEBHOOK_SECRET in .env)
    python apps/adw_server/main.py

    # Run with uvicorn directly
    uvicorn apps.adw_server.server:app --host 0.0.0.0 --port 8000

    # Run with auto-reload for development
    uvicorn apps.adw_server.server:app --reload

Environment Variables:
    See .env.example for required configuration, including:
    - GITHUB_WEBHOOK_SECRET (required)
    - SERVER_HOST (default: 0.0.0.0)
    - SERVER_PORT (default: 8000)
    - ADW_WORKING_DIR (default: current directory)

Endpoints:
    GET  /                      - Redirect to camera app
    POST /                      - GitHub webhook receiver (primary endpoint)
    GET  /health                - Health check
    GET  /health/ready          - Readiness check
    POST /webhooks/github       - GitHub webhook receiver (alternative endpoint)
    GET  /app or /app/          - Camera app (served from static files)
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# Add adw_server directory to path so core modules can be imported
adw_server_dir = os.path.dirname(os.path.abspath(__file__))
if adw_server_dir not in sys.path:
    sys.path.insert(0, adw_server_dir)

from core.config import get_config
from core.handlers import (
    validate_webhook_signature,
    handle_issue_event,
    handle_pull_request_event,
    IssueWebhookPayload,
    PullRequestWebhookPayload,
)


# Configure logging
def setup_logging(log_level: str = "INFO"):
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events.

    Startup:
        - Load and validate configuration
        - Set up logging
        - Verify ADW modules are accessible

    Shutdown:
        - Clean up resources (if needed)
    """
    # Startup
    logger = logging.getLogger("webhook_server")
    logger.info("Starting FastAPI webhook server...")

    try:
        config = get_config()
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Working directory: {config.adw_working_dir}")
        logger.info(f"Static files: {config.static_files_dir}")
        logger.info(f"Environment: {config.environment}")

        # Verify ADW modules are accessible
        try:
            from core.adw_integration import generate_adw_id
            test_id = generate_adw_id()
            logger.info(f"ADW modules verified (test ID: {test_id})")
        except Exception as e:
            logger.error(f"Failed to verify ADW modules: {e}")
            raise

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down FastAPI webhook server...")


# Create FastAPI application
app = FastAPI(
    title="ADW Webhook Server",
    description="GitHub webhook integration and anti-procrastination app server",
    version="1.0.0",
    lifespan=lifespan,
)

# Load configuration and set up logging
config = get_config()
setup_logging(config.log_level)
logger = logging.getLogger("webhook_server")


# Add CORS middleware if enabled
if config.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS enabled with origins: {config.cors_origins}")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"{request.method} {request.url.path} - Status: {response.status_code}")
    return response


# Root endpoint - redirect to camera app
@app.get("/", response_class=RedirectResponse, status_code=302)
async def root():
    """Redirect root to camera app."""
    return RedirectResponse(url="/app")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint.

    Returns server status and configuration info.

    Returns:
        JSON response with status: ok
    """
    return JSONResponse(
        content={
            "status": "ok",
            "service": "adw-webhook-server",
            "environment": config.environment,
        }
    )


@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint.

    Verifies that the server is ready to handle requests by checking:
    - Configuration is loaded
    - ADW modules are accessible
    - Working directory exists

    Returns:
        JSON response with status: ready

    Raises:
        HTTPException: 503 if server is not ready
    """
    try:
        # Verify config
        if not config:
            raise Exception("Configuration not loaded")

        # Verify working directory exists
        if not os.path.isdir(config.adw_working_dir):
            raise Exception(f"Working directory does not exist: {config.adw_working_dir}")

        # Verify ADW modules
        from core.adw_integration import generate_adw_id
        test_id = generate_adw_id()

        return JSONResponse(
            content={
                "status": "ready",
                "working_dir": config.adw_working_dir,
                "static_dir": config.static_files_dir,
            }
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Server not ready: {str(e)}"
        )


# Shared webhook processing logic
async def process_github_webhook(request: Request):
    """Process GitHub webhook events.

    This function contains the shared logic for validating and processing
    GitHub webhook events. It is used by both the root endpoint (/) and
    the /webhooks/github endpoint for backward compatibility.

    Args:
        request: FastAPI Request object containing webhook payload

    Returns:
        JSONResponse with processing status

    Raises:
        HTTPException: 401 if signature is invalid
        HTTPException: 400 if payload is invalid
        HTTPException: 500 if processing fails
    """
    # Get event type from header
    event_type = request.headers.get("X-GitHub-Event")
    if not event_type:
        logger.warning("Webhook request missing X-GitHub-Event header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-GitHub-Event header"
        )

    # Read raw body for signature validation
    body = await request.body()

    # Validate webhook signature
    signature = request.headers.get("X-Hub-Signature-256")
    is_valid = validate_webhook_signature(
        payload_body=body,
        signature_header=signature,
        secret=config.github_webhook_secret,
    )

    if not is_valid:
        logger.warning(f"Invalid webhook signature for event: {event_type}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    logger.info(f"Received valid GitHub webhook: event={event_type}")
    logger.info(f"Webhook payload preview: action={payload.get('action')}, repo={payload.get('repository', {}).get('full_name')}")

    # Route event to appropriate handler
    try:
        if event_type == "issues":
            # Parse and handle issue event
            try:
                issue_payload = IssueWebhookPayload(**payload)
                logger.info(f"✓ Parsed issue webhook: issue=#{issue_payload.issue.number}, action={issue_payload.action}, labels={[l.name for l in issue_payload.issue.labels]}")
            except ValidationError as e:
                logger.error(f"Failed to parse issue payload: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid issue payload: {e}"
                )

            logger.info(f"→ Calling handle_issue_event for issue #{issue_payload.issue.number}")
            result = await handle_issue_event(
                payload=issue_payload,
                working_dir=config.adw_working_dir,
                model=config.adw_default_model,
            )
            logger.info(f"✓ handle_issue_event completed: workflow_triggered={result.get('workflow_triggered')}, adw_id={result.get('adw_id')}")

            return JSONResponse(content=result)

        elif event_type == "pull_request":
            # Parse and handle pull request event
            try:
                pr_payload = PullRequestWebhookPayload(**payload)
            except ValidationError as e:
                logger.error(f"Failed to parse PR payload: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid PR payload: {e}"
                )

            result = await handle_pull_request_event(
                payload=pr_payload,
                working_dir=config.adw_working_dir,
                model=config.adw_default_model,
            )

            return JSONResponse(content=result)

        else:
            # Unsupported event type
            logger.info(f"Ignoring unsupported event type: {event_type}")
            return JSONResponse(
                content={
                    "status": "ignored",
                    "reason": f"Event type not supported: {event_type}",
                    "event_type": event_type,
                }
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


# GitHub webhook endpoints
# Primary endpoint at root path - matches GitHub's default configuration
@app.post("/")
async def github_webhook_root(request: Request):
    """GitHub webhook receiver endpoint at root path.

    This is the primary endpoint for GitHub webhooks. GitHub webhooks are
    often configured to POST to the root path (/), so this endpoint handles
    those requests.

    Headers:
        X-GitHub-Event: Event type (issues, pull_request, etc.)
        X-Hub-Signature-256: Webhook signature for validation

    Request Body:
        JSON payload from GitHub webhook

    Returns:
        JSON response with processing status

    Raises:
        HTTPException: 401 if signature is invalid
        HTTPException: 400 if payload is invalid
        HTTPException: 500 if processing fails
    """
    return await process_github_webhook(request)


# Alternative endpoint for backward compatibility
@app.post("/webhooks/github")
async def github_webhook(request: Request):
    """GitHub webhook receiver endpoint (alternative path).

    This endpoint provides backward compatibility for integrations that
    were configured to use /webhooks/github. Both this endpoint and the
    root POST endpoint (/) use the same processing logic.

    Headers:
        X-GitHub-Event: Event type (issues, pull_request, etc.)
        X-Hub-Signature-256: Webhook signature for validation

    Request Body:
        JSON payload from GitHub webhook

    Returns:
        JSON response with processing status

    Raises:
        HTTPException: 401 if signature is invalid
        HTTPException: 400 if payload is invalid
        HTTPException: 500 if processing fails
    """
    return await process_github_webhook(request)


# Mount static files for camera app
try:
    static_path = config.get_absolute_static_path()
    if os.path.isdir(static_path):
        # Mount the dist folder as /app so React can load its assets
        app.mount("/app", StaticFiles(directory=static_path, html=True), name="app-static")
        logger.info(f"React app mounted from: {static_path}")

        # Also mount the old static folder if it exists (for backwards compatibility with video file)
        old_static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "apps", "static")
        if os.path.isdir(old_static_path):
            app.mount("/static", StaticFiles(directory=old_static_path), name="static")
            logger.info(f"Legacy static files mounted from: {old_static_path}")
    else:
        logger.warning(f"Static files directory not found: {static_path}")
        logger.warning("Camera app will not be available")

except Exception as e:
    logger.error(f"Failed to mount static files: {e}")
    logger.warning("Camera app will not be available")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Path not found: {request.url.path}",
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server Error."""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }
    )


# Main entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn

    try:
        logger.info(f"Starting server on {config.server_host}:{config.server_port}")
        uvicorn.run(
            "apps.webhook_server:app",
            host=config.server_host,
            port=config.server_port,
            log_level=config.log_level.lower(),
            reload=not config.is_production(),
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
