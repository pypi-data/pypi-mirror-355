# pragma: no cover
"""Async HuggingFace Spaces migration functionality."""

import asyncio
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from huggingface_hub import hf_hub_download, list_repo_files
from loguru import logger
from rich import print as rprint


class HuggingFaceSpacesMigrator:
    """Async-first HuggingFace Spaces to Modal migrator."""

    def __init__(self):
        self.client = httpx.AsyncClient()

    async def extract_space_info_async(self, spaces_url: str) -> dict[str, Any]:
        """Extract space information from HuggingFace URL (async)."""
        # Parse URL to get repo_id
        parsed = urlparse(spaces_url)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) < 2 or path_parts[0] != "spaces":
            raise ValueError(f"Invalid HuggingFace Spaces URL: {spaces_url}")

        repo_id = f"{path_parts[1]}/{path_parts[2]}"

        # Get space info via API
        try:
            response = await self.client.get(f"https://huggingface.co/api/spaces/{repo_id}")
            response.raise_for_status()
            space_data = response.json()

            return {
                "repo_id": repo_id,
                "title": space_data.get("title", repo_id),
                "sdk": space_data.get("sdk", "gradio"),
                "python_version": space_data.get("python_version", "3.11"),
                "url": spaces_url,
            }
        except Exception as e:
            logger.warning(f"Could not fetch space metadata: {e}")
            return {
                "repo_id": repo_id,
                "title": repo_id,
                "sdk": "gradio",  # Assume Gradio
                "python_version": "3.11",
                "url": spaces_url,
            }

    async def download_space_files_async(self, space_info: dict[str, Any]) -> Path:
        """Download HuggingFace Space files (async)."""
        repo_id = space_info["repo_id"]
        local_dir = Path(f"./downloaded_spaces/{repo_id.replace('/', '_')}")

        # Create directory
        local_dir.mkdir(parents=True, exist_ok=True)

        # Get list of files
        try:
            files = list_repo_files(repo_id, repo_type="space")

            # Download key files
            key_files = ["app.py", "requirements.txt", "README.md", "config.yaml"]

            for file_path in files:
                if any(file_path.endswith(key_file) for key_file in key_files):
                    try:
                        downloaded_path = await asyncio.to_thread(
                            hf_hub_download,
                            repo_id=repo_id,
                            filename=file_path,
                            repo_type="space",
                            local_dir=local_dir,
                            local_dir_use_symlinks=False,
                        )
                        logger.debug(f"Downloaded: {downloaded_path}")
                    except Exception as e:
                        logger.warning(f"Could not download {file_path}: {e}")

            return local_dir

        except Exception as e:
            logger.error(f"Error downloading space files: {e}")
            raise

    async def convert_to_modal_async(self, local_dir: Path, optimized: bool = True) -> Path:
        """Convert HuggingFace Space to Modal deployment (async)."""
        app_file = local_dir / "app.py"

        if not app_file.exists():
            raise FileNotFoundError(f"app.py not found in {local_dir}")

        # Read the original app
        original_content = await asyncio.to_thread(app_file.read_text, encoding="utf-8")

        # Analyze requirements
        requirements_file = local_dir / "requirements.txt"
        extra_packages = []
        if requirements_file.exists():
            requirements_content = await asyncio.to_thread(requirements_file.read_text, encoding="utf-8")
            extra_packages = [line.strip() for line in requirements_content.split("\n") if line.strip() and not line.startswith("#")]

        # Generate Modal deployment
        mode = "optimized" if optimized else "minimum"
        deployment_file = local_dir / f"modal_deployment.py"

        # Base packages
        if mode == "minimum":
            base_packages = ["gradio>=4.0.0", "fastapi[standard]>=0.100.0", "uvicorn>=0.20.0"]
        else:
            base_packages = [
                "gradio>=4.0.0",
                "fastapi[standard]>=0.100.0",
                "uvicorn>=0.20.0",
                "torch>=2.0.0",
                "transformers>=4.20.0",
                "accelerate>=0.20.0",
                "diffusers>=0.20.0",
                "pillow>=9.0.0",
                "numpy>=1.21.0",
                "pandas>=1.3.0",
            ]

        # Combine packages
        all_packages = base_packages + extra_packages
        packages_str = ",\n    ".join(f'"{pkg}"' for pkg in all_packages)

        # GPU configuration
        gpu_config = 'gpu="any",' if optimized else ""

        # Create deployment template
        deployment_template = f'''
import modal
from fastapi import FastAPI
import gradio as gr
from gradio.routes import mount_gradio_app

# Create Modal app
app = modal.App("modal-for-noobs-hf-migration")

# Configure image with all dependencies
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    {packages_str}
)

# Original HuggingFace Space code
{original_content}

@app.function(
    image=image,
    {gpu_config}
    min_containers=1,
    max_containers=1,  # Single container for sticky sessions
    timeout=3600,
    scaledown_window=60 * 20
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def deploy_gradio():
    """Deploy migrated HuggingFace Space with Modal"""

    # Find the demo object from the original code
    demo = None

    # Try common variable names
    for var_name in ["demo", "app", "interface", "iface"]:
        if var_name in globals():
            potential_demo = globals()[var_name]
            if hasattr(potential_demo, 'queue') and hasattr(potential_demo, 'launch'):
                demo = potential_demo
                break

    if demo is None:
        # Scan all globals for Gradio interfaces
        for var_name, var_value in globals().items():
            if hasattr(var_value, 'queue') and hasattr(var_value, 'launch'):
                demo = var_value
                break

    if demo is None:
        raise ValueError("Could not find Gradio interface in the migrated code")

    # Enable queuing for concurrent requests
    demo.queue(max_size=10)

    # Mount Gradio app to FastAPI
    fastapi_app = FastAPI(title="Migrated HuggingFace Space")
    return mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    app.run()
'''

        # Write deployment file
        await asyncio.to_thread(deployment_file.write_text, deployment_template.strip(), encoding="utf-8")

        return deployment_file

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
