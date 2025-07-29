"""Enhanced GitHub API integration for Modal examples with advanced features.

Migrated and enhanced functionality from gradio-modal-deploy for comprehensive
GitHub repository interaction, deployment history, and repository management.
"""

import asyncio
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


class GitHubAPI:
    """Enhanced async GitHub API client for Modal examples with advanced functionality."""

    def __init__(self, repo: str = "modal-labs/modal-examples", token: str | None = None):
        """Initialize GitHub API client.

        Args:
            repo: GitHub repository in format "owner/repo"
            token: Optional GitHub API token for authenticated requests
        """
        self.repo = repo
        self.owner, self.repo_name = repo.split("/")
        self.base_url = "https://api.github.com"

        # Set up HTTP client with authentication if provided
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self.client = httpx.AsyncClient(timeout=30.0, headers=headers)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_repo_contents(self, path: str = "") -> list[dict[str, Any]]:
        """Get repository contents for a specific path."""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo_name}/contents/{path}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch repo contents for path '{path}': {e}")
            return []

    async def get_file_content(self, path: str) -> str:
        """Get the content of a specific file."""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo_name}/contents/{path}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            return data.get("content", "")

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch file content for '{path}': {e}")
            return ""

    async def get_all_folders(self) -> list[dict[str, str]]:
        """Get all folders in the repository root with enhanced metadata."""
        contents = await self.get_repo_contents()

        folders = []
        for item in contents:
            if item.get("type") == "dir":
                folders.append(
                    {
                        "name": item["name"],
                        "path": item["path"],
                        "url": item.get("html_url", ""),
                        "download_url": item.get("download_url"),
                    }
                )

        return sorted(folders, key=lambda x: x["name"])

    async def get_python_files_in_folder(self, folder_path: str) -> list[dict[str, str]]:
        """Get all Python files in a specific folder with enhanced metadata."""
        contents = await self.get_repo_contents(folder_path)

        python_files = []
        for item in contents:
            if item.get("type") == "file" and item["name"].endswith(".py"):
                python_files.append(
                    {
                        "name": item["name"],
                        "path": item["path"],
                        "size": item.get("size", 0),
                        "url": item.get("html_url", ""),
                        "download_url": item.get("download_url"),
                        "sha": item.get("sha", ""),
                    }
                )

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
                files.append(
                    {
                        "name": item["name"],
                        "path": item["path"],
                        "size": item.get("size", 0),
                        "url": item.get("html_url", ""),
                        "download_url": item.get("download_url"),
                    }
                )
            elif item.get("type") == "dir" and folder_path == "":
                # Recursively search in subdirectories (only one level deep for performance)
                subfolder_files = await self.search_files_by_extension(extension, item["path"])
                files.extend(subfolder_files)

        return sorted(files, key=lambda x: x["name"])

    async def get_repository_info(self) -> dict[str, Any]:
        """Get general repository information."""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo_name}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()
            return {
                "name": data.get("name", ""),
                "full_name": data.get("full_name", ""),
                "description": data.get("description", ""),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "language": data.get("language", ""),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "homepage": data.get("homepage", ""),
                "topics": data.get("topics", []),
                "license": data.get("license", {}).get("name", "") if data.get("license") else "",
            }
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch repository info: {e}")
            return {}

    async def get_recent_commits(self, limit: int = 10, path: str = "") -> list[dict[str, Any]]:
        """Get recent commits for the repository or specific path."""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo_name}/commits"
        params = {"per_page": limit}
        if path:
            params["path"] = path

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            commits = []
            for commit_data in response.json():
                commit = commit_data.get("commit", {})
                commits.append(
                    {
                        "sha": commit_data.get("sha", "")[:7],  # Short SHA
                        "message": commit.get("message", ""),
                        "author": commit.get("author", {}).get("name", ""),
                        "date": commit.get("author", {}).get("date", ""),
                        "url": commit_data.get("html_url", ""),
                    }
                )

            return commits
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch recent commits: {e}")
            return []

    async def get_file_history(self, file_path: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get commit history for a specific file."""
        return await self.get_recent_commits(limit=limit, path=file_path)

    async def download_file(self, file_path: str, local_path: Path) -> bool:
        """Download a file from the repository to local path."""
        content = await self.get_file_content(file_path)
        if not content:
            return False

        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(content)
            logger.info(f"Downloaded {file_path} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {file_path}: {e}")
            return False

    async def get_repository_stats(self) -> dict[str, Any]:
        """Get repository statistics including language breakdown."""
        # Get languages
        languages_url = f"{self.base_url}/repos/{self.owner}/{self.repo_name}/languages"

        try:
            response = await self.client.get(languages_url)
            response.raise_for_status()
            languages = response.json()

            # Calculate language percentages
            total_bytes = sum(languages.values())
            language_stats = []

            for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                language_stats.append({"language": lang, "bytes": bytes_count, "percentage": round(percentage, 1)})

            return {
                "languages": language_stats,
                "total_bytes": total_bytes,
                "primary_language": language_stats[0]["language"] if language_stats else "Unknown",
            }

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch repository stats: {e}")
            return {"languages": [], "total_bytes": 0, "primary_language": "Unknown"}

    async def search_code(self, query: str, file_extension: str = "") -> list[dict[str, Any]]:
        """Search for code within the repository."""
        search_query = f"{query} repo:{self.owner}/{self.repo_name}"
        if file_extension:
            search_query += f" extension:{file_extension}"

        url = f"{self.base_url}/search/code"
        params = {"q": search_query, "per_page": 20}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            results = []
            for item in response.json().get("items", []):
                results.append(
                    {
                        "name": item.get("name", ""),
                        "path": item.get("path", ""),
                        "url": item.get("html_url", ""),
                        "repository": item.get("repository", {}).get("full_name", ""),
                        "score": item.get("score", 0),
                    }
                )

            return results
        except httpx.HTTPError as e:
            logger.error(f"Failed to search code: {e}")
            return []


class ModalExamplesAPI(GitHubAPI):
    """Specialized GitHub API client for Modal examples with additional features."""

    def __init__(self, token: str | None = None):
        """Initialize with Modal examples repository."""
        super().__init__(repo="modal-labs/modal-examples", token=token)

    async def get_example_categories(self) -> list[dict[str, Any]]:
        """Get example categories with metadata."""
        folders = await self.get_all_folders()

        categories = []
        for folder in folders:
            # Get README for category description
            readme_content = await self.get_readme_content(folder["path"])

            # Get Python files count
            python_files = await self.get_python_files_in_folder(folder["path"])

            categories.append(
                {
                    "name": folder["name"],
                    "path": folder["path"],
                    "description": self._extract_description_from_readme(readme_content),
                    "file_count": len(python_files),
                    "files": python_files,
                    "readme": readme_content,
                }
            )

        return categories

    def _extract_description_from_readme(self, readme_content: str) -> str:
        """Extract description from README content."""
        if not readme_content:
            return "No description available"

        lines = readme_content.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 20:
                return line[:200] + "..." if len(line) > 200 else line

        return "No description available"

    async def get_popular_examples(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get popular examples based on file size and recency."""
        all_files = await self.search_files_by_extension(".py")

        # Sort by size (assuming larger files are more comprehensive examples)
        popular = sorted(all_files, key=lambda x: x.get("size", 0), reverse=True)[:limit]

        # Add additional metadata
        for example in popular:
            # Get recent commits for this file
            commits = await self.get_file_history(example["path"], limit=3)
            example["recent_commits"] = commits
            example["last_updated"] = commits[0]["date"] if commits else ""

        return popular

    async def validate_example_for_modal(self, file_path: str) -> dict[str, Any]:
        """Validate if an example is suitable for Modal deployment."""
        content = await self.get_file_content(file_path)

        if not content:
            return {"valid": False, "reason": "Could not fetch file content"}

        # Check for Modal-specific patterns
        has_gradio = "import gradio" in content or "from gradio" in content
        has_modal = "import modal" in content or "from modal" in content
        has_main_block = "if __name__" in content
        has_fastapi = "FastAPI" in content or "from fastapi" in content

        # Check for ML libraries
        ml_libraries = ["torch", "tensorflow", "transformers", "sklearn", "numpy", "pandas"]
        detected_ml = [lib for lib in ml_libraries if lib in content]

        # Determine deployment compatibility
        if has_modal:
            deployment_ready = True
            reason = "Already Modal-compatible"
            suggested_mode = "optimized" if detected_ml else "minimum"
        elif has_gradio:
            deployment_ready = True
            reason = "Gradio app - can be deployed with modal-for-noobs"
            suggested_mode = "optimized" if detected_ml else "minimum"
        else:
            deployment_ready = False
            reason = "Not a Gradio app - requires modification"
            suggested_mode = "minimum"

        return {
            "valid": deployment_ready,
            "reason": reason,
            "suggested_mode": suggested_mode,
            "has_gradio": has_gradio,
            "has_modal": has_modal,
            "has_fastapi": has_fastapi,
            "has_main_block": has_main_block,
            "detected_ml_libraries": detected_ml,
            "file_size": len(content),
            "line_count": len(content.split("\n")),
        }


# Global instances for easy access
github_api = GitHubAPI()
modal_examples_api = ModalExamplesAPI()
