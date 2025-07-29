"""Enhanced Modal deployment functionality with advanced features from gradio-modal-deploy.

This module provides comprehensive Modal deployment capabilities including:
- Advanced deployment modes with GPU and environment configuration
- Environment variables and secrets management
- Custom deployment schedules and timeouts
- Real-time deployment monitoring and management
- Resource optimization and scaling configuration
- Integration with Modal's advanced container features
"""

import asyncio
import base64
import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from rich import print as rprint

# Import Modal's official color palette from common module
from modal_for_noobs.cli_helpers.common import MODAL_DARK_GREEN, MODAL_GREEN, MODAL_LIGHT_GREEN
from modal_for_noobs.config_loader import config_loader
from modal_for_noobs.templates.deployment import (
    generate_modal_deployment,
    generate_modal_deployment_legacy,
    get_image_config,
)


@dataclass
class DeploymentConfig:
    """Advanced deployment configuration with environment management."""

    # Basic configuration
    mode: str = "minimum"
    timeout_minutes: int = 60
    gpu_type: str | None = None
    cpu_count: int | None = None
    memory_gb: int | None = None

    # Environment and secrets
    environment_variables: dict[str, str] = field(default_factory=dict)
    secrets: list[str] = field(default_factory=list)

    # Container configuration
    min_containers: int = 1
    max_containers: int = 10
    concurrent_inputs: int = 1
    scaledown_window: int = 1200  # 20 minutes

    # Storage and volumes
    volume_mounts: dict[str, str] = field(default_factory=dict)
    persistent_storage: bool = False

    # Networking
    allow_cross_origin: bool = True
    custom_domain: str | None = None

    # Advanced features
    schedule: str | None = None  # Cron schedule for periodic runs
    webhook_url: str | None = None  # Webhook for notifications
    auto_scale: bool = True
    keep_warm: bool = False

    # Requirements and packages
    requirements_path: Path | None = None
    custom_packages: list[str] = field(default_factory=list)
    system_packages: list[str] = field(default_factory=list)

    # Deployment metadata
    app_name: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "timeout_minutes": self.timeout_minutes,
            "gpu_type": self.gpu_type,
            "cpu_count": self.cpu_count,
            "memory_gb": self.memory_gb,
            "environment_variables": self.environment_variables,
            "secrets": self.secrets,
            "min_containers": self.min_containers,
            "max_containers": self.max_containers,
            "concurrent_inputs": self.concurrent_inputs,
            "scaledown_window": self.scaledown_window,
            "volume_mounts": self.volume_mounts,
            "persistent_storage": self.persistent_storage,
            "allow_cross_origin": self.allow_cross_origin,
            "custom_domain": self.custom_domain,
            "schedule": self.schedule,
            "webhook_url": self.webhook_url,
            "auto_scale": self.auto_scale,
            "keep_warm": self.keep_warm,
            "requirements_path": str(self.requirements_path) if self.requirements_path else None,
            "custom_packages": self.custom_packages,
            "system_packages": self.system_packages,
            "app_name": self.app_name,
            "description": self.description,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeploymentConfig":
        """Create from dictionary."""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                if key == "requirements_path" and value:
                    setattr(config, key, Path(value))
                else:
                    setattr(config, key, value)
        return config


@dataclass
class DeploymentResult:
    """Result of a Modal deployment operation."""

    success: bool
    url: str | None = None
    app_id: str | None = None
    deployment_file: Path | None = None
    error: str | None = None
    output: str | None = None
    config: DeploymentConfig | None = None
    deployment_time: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "url": self.url,
            "app_id": self.app_id,
            "deployment_file": str(self.deployment_file) if self.deployment_file else None,
            "error": self.error,
            "output": self.output,
            "config": self.config.to_dict() if self.config else None,
            "deployment_time": self.deployment_time,
        }


class ModalAPI:
    """Enhanced async Modal API client for advanced deployment management."""

    def __init__(self, timeout: int = 30):
        """Initialize Modal API client."""
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def list_deployments(self) -> list[dict[str, Any]]:
        """List active Modal deployments with enhanced metadata."""
        try:
            process = await asyncio.create_subprocess_exec(
                "modal", "app", "list", "--json", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                try:
                    # Try to parse JSON output
                    deployments = json.loads(stdout.decode())
                    return deployments if isinstance(deployments, list) else []
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    return await self._parse_deployment_list(stdout.decode())
            else:
                logger.error(f"Failed to list deployments: {stderr.decode()}")
                return []

        except Exception as e:
            logger.error(f"Error listing deployments: {e}")
            return []

    async def _parse_deployment_list(self, output: str) -> list[dict[str, Any]]:
        """Parse deployment list from text output."""
        deployments = []
        lines = output.strip().split("\n")

        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    deployment = {
                        "name": parts[0],
                        "status": parts[1] if len(parts) > 1 else "unknown",
                        "url": self._extract_url_from_line(line),
                        "created_at": parts[2] if len(parts) > 2 else None,
                    }
                    deployments.append(deployment)

        return deployments

    def _extract_url_from_line(self, line: str) -> str | None:
        """Extract URL from a deployment line."""
        if "https://" in line:
            parts = line.split()
            for part in parts:
                if part.startswith("https://"):
                    return part
        return None

    async def kill_deployment(self, app_name: str) -> bool:
        """Kill a specific deployment."""
        try:
            process = await asyncio.create_subprocess_exec(
                "modal", "app", "stop", app_name, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Successfully killed deployment: {app_name}")
                return True
            else:
                logger.error(f"Failed to kill deployment {app_name}: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error killing deployment {app_name}: {e}")
            return False

    async def get_app_logs(self, app_name: str, lines: int = 100) -> str:
        """Get logs for a specific app."""
        try:
            process = await asyncio.create_subprocess_exec(
                "modal", "app", "logs", app_name, "--lines", str(lines), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return stdout.decode()
            else:
                logger.error(f"Failed to get logs for {app_name}: {stderr.decode()}")
                return f"Error getting logs: {stderr.decode()}"

        except Exception as e:
            logger.error(f"Error getting logs for {app_name}: {e}")
            return f"Error getting logs: {e}"

    async def create_secret(self, name: str, value: str) -> bool:
        """Create a Modal secret."""
        try:
            process = await asyncio.create_subprocess_exec(
                "modal", "secret", "create", name, value, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Successfully created secret: {name}")
                return True
            else:
                logger.error(f"Failed to create secret {name}: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error creating secret {name}: {e}")
            return False

    async def list_secrets(self) -> list[str]:
        """List available Modal secrets."""
        try:
            process = await asyncio.create_subprocess_exec(
                "modal", "secret", "list", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                secrets = []
                lines = stdout.decode().strip().split("\n")
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        secrets.append(line.split()[0])
                return secrets
            else:
                logger.error(f"Failed to list secrets: {stderr.decode()}")
                return []

        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            return []


class ModalDeployer:
    """Enhanced async-first Modal deployment handler with advanced features."""

    def __init__(self, app_file: Path, mode: str = "minimum", br_huehuehue: bool = False, config: DeploymentConfig | None = None):
        """Initialize the deployer with app file and deployment configuration."""
        self.app_file = app_file
        self.mode = mode
        self.br_huehuehue = br_huehuehue
        self.config_loader = config_loader
        self.modal_api = ModalAPI()

        # Use provided config or create default
        self.config = config or DeploymentConfig(mode=mode, app_name=app_file.stem)

    async def close(self) -> None:
        """Close resources."""
        await self.modal_api.close()

    async def check_modal_auth_async(self) -> bool:
        """Check if Modal is authenticated (async).

        Returns:
            bool: True if authenticated, False otherwise.
        """
        try:
            # Check environment variables
            if os.getenv("MODAL_TOKEN_ID") and os.getenv("MODAL_TOKEN_SECRET"):
                logger.debug("Modal authentication found via environment variables")
                return True

            # Check for modal config file
            modal_config = Path.home() / ".modal.toml"
            if modal_config.exists():
                logger.debug(f"Modal authentication found at {modal_config}")
                return True

            logger.debug("No Modal authentication found")
            return False
        except Exception as e:
            logger.error(f"Error checking Modal authentication: {e}")
            return False

    async def setup_modal_auth_async(self) -> bool:
        """Setup Modal authentication (async).

        Returns:
            bool: True if setup succeeded, False otherwise.
        """
        try:
            logger.info("Running Modal token flow for authentication...")
            from modal_for_noobs.utils.auth import ModalAuthManager

            auth_mgr = ModalAuthManager()
            success = await auth_mgr.setup_token_flow_auth()
            if success:
                rprint(f"[{MODAL_GREEN}]✅ Modal authentication setup complete![/{MODAL_GREEN}]")
                return True
            else:
                rprint("[red]❌ Failed to setup Modal authentication via token flow[/red]")
                return False
        except Exception as e:
            logger.error(f"Unexpected error during modal setup: {e}")
            rprint(f"[red]❌ Unexpected error: {e}[/red]")
            return False

    async def validate_app_file(self, app_file: Path) -> dict[str, Any]:
        """Validate a Gradio app file for Modal deployment."""
        if not app_file.exists():
            return {"valid": False, "error": f"File not found: {app_file}", "recommendations": ["Create the file first"]}

        if not app_file.suffix == ".py":
            return {"valid": False, "error": "File must be a Python file (.py)", "recommendations": ["Rename file with .py extension"]}

        try:
            content = app_file.read_text()

            # Check for Gradio imports
            has_gradio = "import gradio" in content or "from gradio" in content
            has_blocks = "gr.Blocks" in content or "gradio.Blocks" in content
            has_interface = "gr.Interface" in content or "gradio.Interface" in content
            has_launch = ".launch(" in content

            recommendations = []
            warnings = []

            if not has_gradio:
                recommendations.append("Add 'import gradio as gr' to your file")

            if not (has_blocks or has_interface):
                recommendations.append("Create a Gradio interface using gr.Blocks() or gr.Interface()")

            if not has_launch:
                warnings.append("Consider adding .launch() for local testing")

            # Check for common ML libraries
            ml_libraries = ["torch", "tensorflow", "transformers", "sklearn", "numpy", "pandas"]
            detected_ml = [lib for lib in ml_libraries if lib in content]

            if detected_ml:
                recommendations.append(f"Consider using 'optimized' mode for ML libraries: {', '.join(detected_ml)}")

            # Check for Jupyter-related imports
            jupyter_imports = ["jupyter", "notebook", "ipywidgets", "matplotlib", "plotly"]
            detected_jupyter = [lib for lib in jupyter_imports if lib in content]

            if detected_jupyter:
                recommendations.append("Consider using 'gra_jupy' mode for Jupyter features")

            return {
                "valid": has_gradio and (has_blocks or has_interface),
                "has_gradio": has_gradio,
                "has_interface": has_blocks or has_interface,
                "has_launch": has_launch,
                "detected_ml_libraries": detected_ml,
                "detected_jupyter": detected_jupyter,
                "recommendations": recommendations,
                "warnings": warnings,
                "suggested_mode": self._suggest_deployment_mode(detected_ml, detected_jupyter),
            }

        except Exception as e:
            return {"valid": False, "error": f"Failed to read file: {e}", "recommendations": ["Check file permissions and content"]}

    def _suggest_deployment_mode(self, ml_libraries: list[str], jupyter_libraries: list[str]) -> str:
        """Suggest the best deployment mode based on detected libraries."""
        if jupyter_libraries:
            return "gra_jupy"
        if ml_libraries:
            return "optimized"
        return "minimum"

    async def setup_environment_variables(self, env_vars: dict[str, str]) -> bool:
        """Setup environment variables for deployment."""
        try:
            # Environment variables will be passed to the deployment template
            # Modal handles environment variables through the deployment script
            self.config.environment_variables.update(env_vars)
            logger.info(f"Configured {len(env_vars)} environment variables")
            return True
        except Exception as e:
            logger.error(f"Failed to setup environment variables: {e}")
            return False

    async def setup_secrets(self, secrets: list[str]) -> bool:
        """Setup Modal secrets for deployment."""
        try:
            # Verify secrets exist
            available_secrets = await self.modal_api.list_secrets()

            missing_secrets = []
            for secret in secrets:
                if secret not in available_secrets:
                    missing_secrets.append(secret)

            if missing_secrets:
                logger.warning(f"Missing secrets: {missing_secrets}")
                logger.info("Create missing secrets using: modal secret create <name> <value>")
                return False

            self.config.secrets = secrets
            logger.info(f"Configured {len(secrets)} secrets for deployment")
            return True

        except Exception as e:
            logger.error(f"Failed to setup secrets: {e}")
            return False

    async def create_modal_deployment_async(self, app_file: Path, config: DeploymentConfig | None = None) -> Path:
        """Create enhanced Modal deployment file with advanced configuration."""
        deployment_config = config or self.config
        deployment_file = app_file.parent / f"modal_{app_file.stem}.py"

        # Parse requirements.txt if provided
        custom_packages = deployment_config.custom_packages.copy()
        if deployment_config.requirements_path and deployment_config.requirements_path.exists():
            try:
                requirements_content = deployment_config.requirements_path.read_text().strip()
                for line in requirements_content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Remove version numbers and git URLs
                        package_name = (
                            line.split("==")[0]
                            .split(">=")[0]
                            .split("<=")[0]
                            .split("~=")[0]
                            .split("!=")[0]
                            .split(">")[0]
                            .split("<")[0]
                            .split("@")[0]
                            .strip()
                        )
                        if package_name and package_name not in custom_packages:
                            custom_packages.append(package_name)
            except Exception as e:
                logger.warning(f"Could not parse requirements.txt: {e}")

        # Load base packages from config
        package_config = config_loader.load_base_packages()
        base_packages_list = package_config.get(deployment_config.mode, package_config.get("minimum", []))

        # Combine base packages with custom ones (avoiding duplicates)
        all_packages = base_packages_list.copy()
        for pkg in custom_packages:
            pkg_clean = pkg.lower()
            if not any(pkg_clean in base_pkg.lower() for base_pkg in base_packages_list):
                all_packages.append(pkg)

        # Create enhanced image configuration
        image_config = self._get_enhanced_image_config(deployment_config.mode, all_packages, deployment_config.system_packages)

        # Read the original app code
        original_code = app_file.read_text()

        # Generate enhanced deployment using template system
        deployment_template = self._generate_enhanced_deployment(
            app_file=app_file,
            original_code=original_code,
            config=deployment_config,
            image_config=image_config,
        )

        # Write deployment file (async file writing)
        def write_file():
            with open(deployment_file, "w") as f:
                f.write(deployment_template.strip())

        await asyncio.to_thread(write_file)

        rprint(f"[{MODAL_GREEN}]✅ Created enhanced deployment file: {deployment_file}[/{MODAL_GREEN}]")
        return deployment_file

    def _get_enhanced_image_config(self, mode: str, packages: list[str], system_packages: list[str] = None) -> str:
        """Get enhanced image configuration using the template system."""
        system_packages = system_packages or []

        # Use the existing template system's image configuration
        base_config = get_image_config(mode, packages)

        # If we have additional system packages, enhance the base config
        if system_packages:
            system_pkgs_str = '", "'.join(system_packages)
            # Add system packages to the base configuration
            if ".pip_install(" in base_config:
                # Insert apt_install before pip_install
                base_config = base_config.replace(".pip_install(", f'.apt_install("{system_pkgs_str}").pip_install(')
            else:
                # Add apt_install to the end
                base_config = base_config.rstrip(")") + f'.apt_install("{system_pkgs_str}")'

        return base_config

    def _generate_enhanced_deployment(self, app_file: Path, original_code: str, config: DeploymentConfig, image_config: str) -> str:
        """Generate enhanced deployment using the template system with advanced Modal features."""
        # Check if we have advanced configuration that requires custom template
        has_advanced_config = (
            config.environment_variables
            or config.secrets
            or config.gpu_type
            or config.volume_mounts
            or config.cpu_count
            or config.memory_gb
            or config.min_containers != 1
            or config.max_containers != 10
            or config.concurrent_inputs != 1
        )

        if not has_advanced_config:
            # Use the standard template system
            return generate_modal_deployment(
                app_file=app_file,
                original_code=original_code,
                deployment_mode=config.mode,
                timeout_seconds=config.timeout_minutes * 60,
                scaledown_window=config.scaledown_window,
                image_config=image_config,
            )

        # For advanced configurations, create enhanced template
        return self._create_enhanced_template(app_file=app_file, original_code=original_code, config=config, image_config=image_config)

    def _create_enhanced_template(self, app_file: Path, original_code: str, config: DeploymentConfig, image_config: str) -> str:
        """Create enhanced template with advanced Modal features."""
        # Build function parameters dynamically
        function_params = ["image=image"]

        # GPU configuration
        if config.gpu_type:
            if config.gpu_type == "any":
                function_params.append('gpu="any"')
            else:
                function_params.append(f'gpu="{config.gpu_type}"')

        # Resource configuration
        if config.cpu_count:
            function_params.append(f"cpu={config.cpu_count}")
        if config.memory_gb:
            function_params.append(f"memory={config.memory_gb * 1024}")

        # Container scaling
        function_params.extend(
            [
                f"min_containers={config.min_containers}",
                f"max_containers={config.max_containers}",
                f"timeout={config.timeout_minutes * 60}",
                f"scaledown_window={config.scaledown_window}",
            ]
        )

        # Environment variables
        if config.environment_variables:
            env_items = [f'"{k}": "{v}"' for k, v in config.environment_variables.items()]
            # Fix f-string backslash issue by preprocessing multiline string
            newline = "\n"
            indent = "        "
            env_joined = f",{newline}{indent}".join(env_items)
            environment_block = f"environment={{{newline}{indent}{env_joined}{newline}    }}"
            function_params.append(environment_block)

        # Secrets
        if config.secrets:
            secrets_list = [f'modal.Secret.from_name("{secret}")' for secret in config.secrets]
            function_params.append(f"secrets=[{', '.join(secrets_list)}]")

        # Volume mounts
        if config.volume_mounts:
            volume_items = []
            for mount_path, volume_name in config.volume_mounts.items():
                volume_items.append(f'"{mount_path}": modal.Volume.from_name("{volume_name}")')
            # Fix f-string backslash issue by preprocessing multiline string
            newline = "\n"
            indent = "        "
            volumes_joined = f",{newline}{indent}".join(volume_items)
            volumes_block = f"volumes={{{newline}{indent}{volumes_joined}{newline}    }}"
            function_params.append(volumes_block)

        # Keep warm
        if config.keep_warm:
            function_params.append("keep_warm=True")

        # Build template components
        mode_info = config.mode
        gpu_info = config.gpu_type or "CPU only"
        container_info = f"{config.min_containers}-{config.max_containers}"
        timeout_info = f"{config.timeout_minutes}min"

        # Build app configuration
        app_name_expr = config.app_name or str(app_file.stem)
        if config.description:
            app_description = config.description
        else:
            app_description = f"Enhanced Gradio deployment from {app_file.name}"

        # Build function parameters string
        function_params_str = ",\n    ".join(function_params)

        # Build deployment info
        env_count = len(config.environment_variables)
        secrets_count = len(config.secrets)
        cpu_info = config.cpu_count or "auto"
        memory_info = f"{config.memory_gb or 'auto'} GB RAM" if config.memory_gb else "auto"
        gpu_accel = config.gpu_type or "disabled"

        # Build concurrent inputs
        queue_size = config.concurrent_inputs * 10

        # Import template constants
        from modal_for_noobs.templates.template_constants import APP_EXECUTION, DEMO_QUEUE_CONFIG, GRADIO_DETECTION, MODAL_IMPORTS

        # Build template using safe string concatenation
        header_section = f"""# 🚀 Enhanced Modal Deployment Script
# Generated by modal-for-noobs with advanced configuration
# Mode: {mode_info} | GPU: {gpu_info}
# Containers: {container_info} | Timeout: {timeout_info}

{MODAL_IMPORTS}

# Enhanced Modal app configuration
app = modal.App(
    "{app_name_expr}",
    description="{app_description}"
)

# Enhanced image configuration
image = {image_config}

# Original Gradio application code
{original_code}

# Enhanced Modal function with advanced configuration
@app.function(
    {function_params_str}
)
@modal.concurrent(max_inputs={config.concurrent_inputs})
@modal.asgi_app()
def deploy_gradio():
    \"\"\"
    Enhanced Modal deployment with advanced features:
    - Environment variables: {env_count} configured
    - Secrets management: {secrets_count} secrets
    - Custom scaling: {container_info} containers
    - Resource optimization: {cpu_info} CPU, {memory_info}
    - GPU acceleration: {gpu_accel}
    \"\"\"
    
    # Log deployment configuration
    logger.info("Starting enhanced Modal deployment: {app_name_expr}")
    logger.info("Mode: {mode_info} | GPU: {gpu_info}")
    
    {GRADIO_DETECTION}
    
    {DEMO_QUEUE_CONFIG.replace("20", str(queue_size))}
    
    # Enhanced FastAPI integration
    fastapi_app = FastAPI(
        title="{app_name_expr}",
        description="{app_description}",
        version="1.0.0",
        docs_url="/docs" if {str(config.allow_cross_origin).lower()} else None,
        redoc_url="/redoc" if {str(config.allow_cross_origin).lower()} else None
    )
    
    logger.info("Enhanced deployment configured successfully")
    return mount_gradio_app(fastapi_app, demo, path="/")

{APP_EXECUTION}
"""

        template = header_section

        return template

    async def deploy_to_modal_async(self, deployment_file: Path, config: DeploymentConfig | None = None) -> DeploymentResult:
        """Deploy to Modal with enhanced error handling and result tracking."""
        deployment_config = config or self.config
        start_time = asyncio.get_event_loop().time()

        try:
            # Enhanced deployment command with additional flags
            cmd = ["modal", "deploy", str(deployment_file)]

            # Add deployment-specific flags
            if deployment_config.app_name:
                cmd.extend(["--name", deployment_config.app_name])

            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()

            deployment_time = asyncio.get_event_loop().time() - start_time
            output = stdout.decode()
            error_output = stderr.decode()

            if process.returncode != 0:
                logger.error(f"Deployment failed with exit code {process.returncode}")
                return DeploymentResult(
                    success=False,
                    error=error_output,
                    output=output,
                    deployment_file=deployment_file,
                    config=deployment_config,
                    deployment_time=deployment_time,
                )

            # Extract URL and app ID from output
            url = self._extract_url_from_output(output)
            app_id = self._extract_app_id_from_output(output)

            logger.success(f"Deployment successful in {deployment_time:.2f}s")

            return DeploymentResult(
                success=True,
                url=url,
                app_id=app_id,
                deployment_file=deployment_file,
                output=output,
                config=deployment_config,
                deployment_time=deployment_time,
            )

        except Exception as e:
            deployment_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Deployment error after {deployment_time:.2f}s: {e}")

            return DeploymentResult(
                success=False, error=str(e), deployment_file=deployment_file, config=deployment_config, deployment_time=deployment_time
            )

    def _extract_url_from_output(self, output: str) -> str | None:
        """Extract deployment URL from Modal output."""
        lines = output.split("\n")
        for line in lines:
            if "https://" in line and "modal.run" in line:
                # Extract just the URL part
                parts = line.split()
                for part in parts:
                    if part.startswith("https://") and "modal.run" in part:
                        return part.rstrip(".,;")
        return None

    def _extract_app_id_from_output(self, output: str) -> str | None:
        """Extract app ID from Modal output."""
        lines = output.split("\n")
        for line in lines:
            if "App ID:" in line or "app-id:" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if "id" in part.lower() and i + 1 < len(parts):
                        return parts[i + 1]
        return None

    async def deploy(self, config: DeploymentConfig | None = None) -> DeploymentResult:
        """Enhanced main deployment method with comprehensive configuration support.

        Returns:
            DeploymentResult: Comprehensive deployment result with metadata.
        """
        deployment_config = config or self.config

        try:
            # Validate app file
            validation = await self.validate_app_file(self.app_file)
            if not validation["valid"]:
                logger.error(f"App validation failed: {validation['error']}")
                return DeploymentResult(success=False, error=f"App validation failed: {validation['error']}", config=deployment_config)

            # Check authentication
            if not await self.check_modal_auth_async():
                logger.info("Modal authentication not found, setting up...")
                if not await self.setup_modal_auth_async():
                    return DeploymentResult(success=False, error="Failed to setup Modal authentication", config=deployment_config)

            # Setup environment variables and secrets
            if deployment_config.environment_variables:
                await self.setup_environment_variables(deployment_config.environment_variables)

            if deployment_config.secrets:
                secrets_ok = await self.setup_secrets(deployment_config.secrets)
                if not secrets_ok:
                    logger.warning("Some secrets are missing, deployment may fail")

            # Create enhanced deployment file
            deployment_file = await self.create_modal_deployment_async(self.app_file, deployment_config)

            # Deploy to Modal with enhanced configuration
            result = await self.deploy_to_modal_async(deployment_file, deployment_config)

            if result.success:
                rprint(f"[{MODAL_GREEN}]🎉 Enhanced deployment successful![/{MODAL_GREEN}]")
                if result.url:
                    rprint(f"[{MODAL_GREEN}]🌐 Your app is live at: {result.url}[/{MODAL_GREEN}]")
                if result.app_id:
                    rprint(f"[{MODAL_LIGHT_GREEN}]📱 App ID: {result.app_id}[/{MODAL_LIGHT_GREEN}]")

                # Display configuration summary
                rprint(f"[{MODAL_LIGHT_GREEN}]⚙️ Configuration:[/{MODAL_LIGHT_GREEN}]")
                rprint(f"  • Mode: {deployment_config.mode}")
                rprint(f"  • GPU: {deployment_config.gpu_type or 'CPU only'}")
                rprint(f"  • Containers: {deployment_config.min_containers}-{deployment_config.max_containers}")
                rprint(f"  • Timeout: {deployment_config.timeout_minutes} minutes")
                if deployment_config.environment_variables:
                    rprint(f"  • Environment variables: {len(deployment_config.environment_variables)}")
                if deployment_config.secrets:
                    rprint(f"  • Secrets: {len(deployment_config.secrets)}")
            else:
                rprint(f"[red]❌ Deployment failed: {result.error}[/red]")

            return result

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return DeploymentResult(success=False, error=str(e), config=deployment_config)

    async def get_deployment_status(self, app_name: str) -> dict[str, Any]:
        """Get comprehensive deployment status and metadata."""
        try:
            deployments = await self.modal_api.list_deployments()

            for deployment in deployments:
                if deployment.get("name") == app_name:
                    # Get additional metadata
                    logs = await self.modal_api.get_app_logs(app_name, lines=10)

                    return {
                        "found": True,
                        "status": deployment.get("status"),
                        "url": deployment.get("url"),
                        "created_at": deployment.get("created_at"),
                        "recent_logs": logs[:500] if logs else "No logs available",
                        "metadata": deployment,
                    }

            return {"found": False, "error": f"App '{app_name}' not found"}

        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {"found": False, "error": str(e)}

    async def kill_deployment(self, app_name: str) -> bool:
        """Kill a deployment with enhanced feedback."""
        try:
            success = await self.modal_api.kill_deployment(app_name)

            if success:
                rprint(f"[{MODAL_GREEN}]✅ Successfully killed deployment: {app_name}[/{MODAL_GREEN}]")
            else:
                rprint(f"[red]❌ Failed to kill deployment: {app_name}[/red]")

            return success

        except Exception as e:
            logger.error(f"Error killing deployment: {e}")
            rprint(f"[red]❌ Error killing deployment: {e}[/red]")
            return False

    def create_deployment_config(
        self,
        mode: str = "minimum",
        gpu_type: str | None = None,
        timeout_minutes: int = 60,
        env_vars: dict[str, str] | None = None,
        secrets: list[str] | None = None,
        **kwargs,
    ) -> DeploymentConfig:
        """Create a deployment configuration with enhanced options."""
        return DeploymentConfig(
            mode=mode,
            gpu_type=gpu_type,
            timeout_minutes=timeout_minutes,
            environment_variables=env_vars or {},
            secrets=secrets or [],
            app_name=self.app_file.stem,
            **kwargs,
        )


# Global instances for enhanced Modal API access
modal_api = ModalAPI()
