"""Enhanced GitHub API integration for Modal examples with advanced features."""

import asyncio
import base64
from pathlib import Path

import httpx
from loguru import logger


class GitHubAPI:
    """Async GitHub API client for Modal examples."""

    BASE_URL = "https://api.github.com"
    REPO_OWNER = "modal-labs"
    REPO_NAME = "modal-examples"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_repo_contents(self, path: str = "") -> list[dict[str, any]]:
        """Get repository contents for a specific path."""
        url = f"{self.BASE_URL}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/contents/{path}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch repo contents for path '{path}': {e}")
            return []

    async def get_file_content(self, path: str) -> str:
        """Get the content of a specific file."""
        url = f"{self.BASE_URL}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/contents/{path}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            else:
                return data.get("content", "")

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch file content for '{path}': {e}")
            return ""

    async def get_all_folders(self) -> list[dict[str, str]]:
        """Get all folders in the repository root."""
        contents = await self.get_repo_contents()

        folders = []
        for item in contents:
            if item.get("type") == "dir":
                folders.append({"name": item["name"], "path": item["path"]})

        return sorted(folders, key=lambda x: x["name"])

    async def get_python_files_in_folder(self, folder_path: str) -> list[dict[str, str]]:
        """Get all Python files in a specific folder."""
        contents = await self.get_repo_contents(folder_path)

        python_files = []
        for item in contents:
            if item.get("type") == "file" and item["name"].endswith(".py"):
                python_files.append({"name": item["name"], "path": item["path"]})

        return sorted(python_files, key=lambda x: x["name"])

    async def get_readme_content(self, folder_path: str = "") -> str:
        """Get README.md content for a folder, with fallback to root README."""
        # Try folder-specific README first
        if folder_path:
            readme_path = f"{folder_path}/README.md"
            content = await self.get_file_content(readme_path)
            if content:
                return content

        # Fallback to root README
        root_readme_content = await self.get_file_content("README.md")
        return root_readme_content

    async def search_files_by_extension(self, extension: str, folder_path: str = "") -> list[dict[str, str]]:
        """Search for files with specific extension in a folder."""
        contents = await self.get_repo_contents(folder_path)

        files = []
        for item in contents:
            if item.get("type") == "file" and item["name"].endswith(extension):
                files.append({"name": item["name"], "path": item["path"]})
            elif item.get("type") == "dir" and folder_path == "":
                # Recursively search in subdirectories (only one level deep for performance)
                subfolder_files = await self.search_files_by_extension(extension, item["path"])
                files.extend(subfolder_files)

        return sorted(files, key=lambda x: x["name"])


# Global GitHub API instance
github_api = GitHubAPI()


# ⚡ Modal Function Configuration
# Engineered for scalability, performance, and reliability
@app.function(
    image=image,
    gpu="any",
    min_containers=1,
    max_containers=1,  # Single container for session consistency and state management
    timeout=3600,  # Configurable timeout for workload requirements
    scaledown_window=1200,  # Optimized scale-down for cost efficiency
)
@modal.concurrent(max_inputs=100)  # High concurrency for production-grade performance
@modal.asgi_app()
def deploy_gradio():
    """Deploy Gradio app with Modal's high-performance infrastructure.

    This deployment function implements:
    - Smart Gradio interface detection using global scope analysis
    - FastAPI integration following Modal's ASGI architecture patterns
    - Performance optimization for concurrent request handling
    - Error handling and fallback mechanisms for production reliability
    """
    # 🔍 Smart Gradio Interface Detection
    # Using global scope analysis for maximum compatibility
    demo = None

    # Primary detection: Check common Gradio interface names
    if "demo" in globals():
        demo = globals()["demo"]
    elif "app" in globals() and hasattr(globals()["app"], "queue"):
        demo = globals()["app"]
    elif "interface" in globals():
        demo = globals()["interface"]
    elif "iface" in globals():
        demo = globals()["iface"]

    # Fallback detection: Comprehensive global scope scan
    if demo is None:
        for var_name, var_value in globals().items():
            if hasattr(var_value, "queue") and hasattr(var_value, "launch"):
                demo = var_value
                break

    # 🚨 Fail-safe error handling with descriptive messaging
    if demo is None:
        raise ValueError(
            "Could not find Gradio interface in the application. "
            "Ensure your app defines a Gradio interface as 'demo', 'app', 'interface', or 'iface'."
        )

    # 🚀 Performance Configuration
    # Optimized queue size for responsiveness and throughput
    demo.queue(max_size=10)

    # 🔗 FastAPI Integration
    # Following Modal's recommended ASGI architecture patterns
    fastapi_app = FastAPI(
        title="Modal-for-noobs Gradio App",
        description="High-performance Gradio deployment on Modal cloud infrastructure",
        version="1.0.0",
        docs_url="/docs",  # Enable API documentation
        redoc_url="/redoc",  # Enable alternative API documentation
    )

    return mount_gradio_app(fastapi_app, demo, path="/")


# 🏃‍♂️ Direct execution support for local testing
if __name__ == "__main__":
    app.run()
