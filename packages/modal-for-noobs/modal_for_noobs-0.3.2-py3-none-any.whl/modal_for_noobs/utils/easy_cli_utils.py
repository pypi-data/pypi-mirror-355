#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "loguru",
# ]
"""Utility helpers for Modal authentication and deployment.

This module provides helper functions extracted from the legacy easy_modal_cli
module for Modal authentication verification, setup, and deployment script generation.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

from loguru import logger


def check_modal_auth() -> bool:
    """Check if Modal authentication is configured.

    Verifies authentication via environment variables (MODAL_TOKEN_ID and
    MODAL_TOKEN_SECRET) or the presence of a local .modal.toml file.

    Returns:
        bool: True if Modal authentication is configured, False otherwise.
    """
    try:
        if os.getenv("MODAL_TOKEN_ID") and os.getenv("MODAL_TOKEN_SECRET"):
            logger.debug("Modal authentication found via environment variables")
            return True

        modal_config_path = Path.home() / ".modal.toml"
        if modal_config_path.exists():
            logger.debug(f"Modal authentication found at {modal_config_path}")
            return True

        logger.debug("No Modal authentication found")
        return False
    except OSError as e:
        logger.error(f"Error checking Modal authentication: {e}")
        return False


def setup_modal_auth() -> bool:
    """Run ``modal setup`` to configure Modal authentication.

    Attempts to execute the modal setup command to configure
    authentication credentials.

    Returns:
        bool: True if setup succeeded, False if it failed.
    """
    try:
        logger.info("Running modal setup...")
        # Use the full path to modal executable if available
        modal_path = subprocess.check_output(["which", "modal"], text=True).strip()
        result = subprocess.run([modal_path, "setup"], check=True, capture_output=True, text=True)
        logger.debug(f"Modal setup output: {result.stdout}")
        logger.success("Modal setup completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Modal setup failed with exit code {e.returncode}: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Modal CLI not found. Please install modal: pip install modal")
        return False
    except OSError as e:
        logger.error(f"OS error during modal setup: {e}")
        return False


async def setup_modal_auth_async() -> bool:
    """Run ``modal setup`` to configure Modal authentication asynchronously.

    Attempts to execute the modal setup command asynchronously to configure
    authentication credentials.

    Returns:
        bool: True if setup succeeded, False if it failed.
    """
    try:
        logger.info("Running modal setup asynchronously...")
        # Get the full path to modal executable
        which_process = await asyncio.create_subprocess_exec(
            "which", "modal", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        which_stdout, _ = await which_process.communicate()
        modal_path = which_stdout.decode().strip()

        if not modal_path:
            logger.error("Modal CLI not found. Please install modal: pip install modal")
            return False

        process = await asyncio.create_subprocess_exec(modal_path, "setup", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.debug(f"Modal setup output: {stdout.decode()}")
            logger.success("Modal setup completed successfully")
            return True

        logger.error(f"Modal setup failed with exit code {process.returncode}: {stderr.decode()}")
        return False
    except FileNotFoundError:
        logger.error("Modal CLI not found. Please install modal: pip install modal")
        return False
    except OSError as e:
        logger.error(f"OS error during modal setup: {e}")
        return False


def create_modal_deployment(app_file: str | Path, deployment_mode: str = "minimum") -> Path:
    """Create a Modal deployment script for a Gradio application.

    Generates a Python deployment script that configures a Modal app
    with appropriate dependencies and settings based on the specified mode.

    Args:
        app_file: Path to the Gradio application file to deploy.
        deployment_mode: Deployment configuration mode. Options:
            - "minimum": Basic dependencies, CPU only
            - "optimized": ML libraries with GPU support

    Returns:
        Path: Path to the generated deployment script file.
    """
    app_path = Path(app_file)
    deployment_file = app_path.parent / f"modal_{app_path.stem}.py"

    if deployment_mode == "minimum":
        image_config = (
            "image = modal.Image.debian_slim(python_version='3.11').pip_install(\n"
            "    'gradio>=4.0.0',\n    'fastapi[standard]>=0.100.0',\n    'uvicorn>=0.20.0'\n)"
        )
    else:
        image_config = (
            "image = modal.Image.debian_slim(python_version='3.11').pip_install(\n"
            "    'gradio>=4.0.0',\n    'fastapi[standard]>=0.100.0',\n    'uvicorn>=0.20.0',\n"
            "    'torch>=2.0.0',\n    'transformers>=4.20.0',\n    'accelerate>=0.20.0',\n"
            "    'diffusers>=0.20.0',\n    'pillow>=9.0.0',\n    'numpy>=1.21.0',\n    'pandas>=1.3.0'\n)"
        )

    gpu_line = "    gpu='any'," if deployment_mode == "optimized" else ""

    deployment_template = f"""# 🚀 Modal Deployment Script
# Generated by modal-for-noobs - https://github.com/arthrod/modal-for-noobs
# Deployment Mode: {deployment_mode}
# Following Modal's technical design philosophy for high-performance cloud computing

import modal
from fastapi import FastAPI
import gradio as gr
from gradio.routes import mount_gradio_app

# 🎯 Create Modal App with descriptive naming
app = modal.App('modal-for-noobs-{app_path.stem}')

# 🐳 Container Image Configuration
# Optimized for {deployment_mode} workloads with efficient dependency management
{image_config}

# ⚡ Function Configuration
# Designed for scalability and performance following Modal best practices
@app.function(
    image=image,{gpu_line}
    min_containers=1,
    max_containers=1,  # Single container for session consistency
    timeout=3600,  # 1 hour timeout for long-running tasks
    scaledown_window=60 * 20,  # 20 minute scale-down window
)
@modal.concurrent(max_inputs=100)  # High concurrency for production workloads
@modal.asgi_app()
def deploy_gradio():
    \"\"\"
    Deploy Gradio app with Modal's high-performance infrastructure.
    
    This function implements smart Gradio interface detection and FastAPI integration
    following Modal's technical architecture patterns.
    \"\"\"
    import sys
    from pathlib import Path

    # 📁 Dynamic path management for modular imports
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

    # 🔍 Smart Gradio interface detection
    import {app_path.stem} as target_module
    demo = None
    
    # Primary detection: Common Gradio interface names
    for attr in ['demo', 'app', 'interface', 'iface']:
        if hasattr(target_module, attr):
            obj = getattr(target_module, attr)
            if hasattr(obj, 'queue') and hasattr(obj, 'launch'):
                demo = obj
                break
    
    # Fallback detection: Scan all module attributes
    if demo is None:
        for attr in dir(target_module):
            if attr.startswith('_'):
                continue
            obj = getattr(target_module, attr)
            if hasattr(obj, 'queue') and hasattr(obj, 'launch'):
                demo = obj
                break
    
    # 🚨 Fail-safe error handling
    if demo is None:
        raise ValueError('Could not find Gradio interface in module')
    
    # 🚀 Configure for high-performance deployment
    demo.queue(max_size=10)  # Optimized queue size for responsiveness
    
    # 🔗 FastAPI integration with Modal's ASGI architecture
    fastapi_app = FastAPI(
        title='Modal-for-noobs Gradio App',
        description='Deployed with modal-for-noobs - High-performance Gradio on Modal',
        version='1.0.0'
    )
    
    return mount_gradio_app(fastapi_app, demo, path='/')

# 🏃‍♂️ Direct execution support
if __name__ == '__main__':
    app.run()
"""

    deployment_file.write_text(deployment_template.strip())
    return deployment_file
