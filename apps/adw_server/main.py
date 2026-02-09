"""Main entry point for the ADW automation server.

This script starts the FastAPI ADW server using uvicorn.

Usage:
    python apps/adw_server/main.py

    # Or with uvicorn directly:
    uvicorn apps.adw_server.server:app --host 0.0.0.0 --port 8000

Environment Variables:
    See .env.example in this directory for configuration options.
"""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def main():
    """Start the ADW automation server."""
    import uvicorn
    from core.config import get_config

    try:
        config = get_config()
        logger.info(f"Starting ADW server on {config.server_host}:{config.server_port}")
        logger.info(f"Environment: {config.environment}")
        logger.info(f"Working directory: {config.adw_working_dir}")

        uvicorn.run(
            "apps.adw_server.server:app",
            host=config.server_host,
            port=config.server_port,
            log_level=config.log_level.lower(),
            reload=not config.is_production(),
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
