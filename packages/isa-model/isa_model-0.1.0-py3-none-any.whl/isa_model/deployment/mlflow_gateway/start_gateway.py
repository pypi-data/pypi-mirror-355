#!/usr/bin/env python3
"""
MLflow Gateway starter script.
Replaces the custom adapter with industry-standard MLflow Gateway.

Usage:
    python -m isa_model.deployment.mlflow_gateway.start_gateway
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def start_mlflow_gateway():
    """Start MLflow Gateway with our configuration."""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    config_file = script_dir / "gateway_config.yaml"
    
    if not config_file.exists():
        logger.error(f"Gateway config file not found: {config_file}")
        sys.exit(1)
    
    # Set environment variables
    os.environ["MLFLOW_GATEWAY_CONFIG_PATH"] = str(config_file)
    
    # MLflow Gateway command
    cmd = [
        "mlflow", "gateway", "start",
        "--config-path", str(config_file),
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    logger.info("🚀 Starting MLflow Gateway...")
    logger.info(f"📁 Config file: {config_file}")
    logger.info(f"🌐 Server: http://localhost:8000")
    logger.info(f"📚 Docs: http://localhost:8000/docs")
    
    try:
        # Start the gateway
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("MLflow Gateway stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"MLflow Gateway failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_mlflow_gateway() 