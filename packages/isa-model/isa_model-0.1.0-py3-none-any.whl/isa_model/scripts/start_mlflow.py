#!/usr/bin/env python
"""
Start an MLflow tracking server.

This script provides a simple way to start an MLflow tracking server
with configurable storage locations.
"""

import os
import argparse
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Start an MLflow tracking server")
    
    parser.add_argument(
        "--backend_store_uri",
        type=str,
        default="./mlruns",
        help="URI for the backend store (e.g., SQLite, MySQL, PostgreSQL)"
    )
    parser.add_argument(
        "--default_artifact_root",
        type=str,
        default="./mlartifacts",
        help="Directory or URI for storing artifacts"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of gunicorn workers"
    )
    
    return parser.parse_args()


def main():
    """Start the MLflow tracking server."""
    args = parse_args()
    
    # Create directories if they don't exist
    if args.backend_store_uri.startswith("./") or args.backend_store_uri.startswith("/"):
        os.makedirs(args.backend_store_uri, exist_ok=True)
        logger.info(f"Using backend store: {args.backend_store_uri}")
    
    if args.default_artifact_root.startswith("./") or args.default_artifact_root.startswith("/"):
        os.makedirs(args.default_artifact_root, exist_ok=True)
        logger.info(f"Using artifact root: {args.default_artifact_root}")
    
    # Build the MLflow command
    cmd = [
        "mlflow", "server",
        "--backend-store-uri", args.backend_store_uri,
        "--default-artifact-root", args.default_artifact_root,
        "--host", args.host,
        "--port", str(args.port),
        "--workers", str(args.workers)
    ]
    
    # Start the server
    logger.info(f"Starting MLflow server: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("MLflow server stopped by user")
    except Exception as e:
        logger.error(f"Error starting MLflow server: {e}")
        raise


if __name__ == "__main__":
    main() 