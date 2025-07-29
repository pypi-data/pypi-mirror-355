"""Enhanced deployment utilities for modal-for-noobs with advanced Modal features."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import uvloop
from loguru import logger
from rich import print as rprint

from modal_for_noobs.modal_deploy import DeploymentConfig, DeploymentResult, ModalAPI, ModalDeployer


def validate_app_file(app_file: str | Path) -> dict[str, Any]:
    """Validate a Gradio app file for Modal deployment.

    Args:
        app_file: Path to the app file to validate

    Returns:
        dict: Validation result with recommendations
    """
    app_path = Path(app_file)

    if not app_path.exists():
        return {"valid": False, "error": f"File not found: {app_path}", "recommendations": ["Create the file first"]}

    if not app_path.suffix == ".py":
        return {"valid": False, "error": "File must be a Python file (.py)", "recommendations": ["Rename file with .py extension"]}

    try:
        content = app_path.read_text()

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
            "suggested_mode": _suggest_deployment_mode(detected_ml, detected_jupyter),
        }

    except Exception as e:
        return {"valid": False, "error": f"Failed to read file: {e!s}", "recommendations": ["Check file permissions and content"]}


# Import Modal's color constants from common module
from modal_for_noobs.cli_helpers.common import MODAL_DARK_GREEN, MODAL_GREEN, MODAL_LIGHT_GREEN


def create_deployment_config(
    mode: str = "minimum",
    gpu_type: str | None = None,
    timeout_minutes: int = 60,
    env_vars: dict[str, str] | None = None,
    secrets: list[str] | None = None,
    app_name: str | None = None,
    **kwargs,
) -> DeploymentConfig:
    """Create a deployment configuration with validation.

    Args:
        mode: Deployment mode (minimum, optimized, gra_jupy, marimo)
        gpu_type: GPU type (any, a100, t4, etc.)
        timeout_minutes: Timeout in minutes
        env_vars: Environment variables dictionary
        secrets: List of Modal secret names
        app_name: Application name
        **kwargs: Additional configuration options

    Returns:
        DeploymentConfig: Validated deployment configuration
    """
    return DeploymentConfig(
        mode=mode,
        gpu_type=gpu_type,
        timeout_minutes=timeout_minutes,
        environment_variables=env_vars or {},
        secrets=secrets or [],
        app_name=app_name,
        **kwargs,
    )


def validate_deployment_config(config: DeploymentConfig) -> dict[str, Any]:
    """Validate deployment configuration.

    Args:
        config: Deployment configuration to validate

    Returns:
        Dict with validation results
    """
    issues = []
    warnings = []

    # Validate mode
    valid_modes = ["minimum", "optimized", "gra_jupy", "marimo"]
    if config.mode not in valid_modes:
        issues.append(f"Invalid mode '{config.mode}'. Valid modes: {', '.join(valid_modes)}")

    # Validate GPU configuration
    if config.gpu_type and config.mode == "minimum":
        warnings.append("GPU specified but mode is 'minimum'. Consider using 'optimized' mode.")

    # Validate timeout
    if config.timeout_minutes < 1 or config.timeout_minutes > 1440:  # 24 hours max
        issues.append("Timeout must be between 1 and 1440 minutes")

    # Validate container scaling
    if config.min_containers < 1:
        issues.append("min_containers must be at least 1")
    if config.max_containers < config.min_containers:
        issues.append("max_containers must be >= min_containers")

    # Validate memory
    if config.memory_gb and (config.memory_gb < 1 or config.memory_gb > 64):
        issues.append("Memory must be between 1 and 64 GB")

    # Validate app name
    if config.app_name and not config.app_name.replace("-", "").replace("_", "").isalnum():
        issues.append("App name must contain only alphanumeric characters, hyphens, and underscores")

    return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings, "config": config.to_dict()}


async def setup_modal_secrets(secrets: list[str]) -> dict[str, bool]:
    """Setup Modal secrets for deployment.

    Args:
        secrets: List of secret names to verify

    Returns:
        Dict mapping secret names to their availability status
    """
    modal_api = ModalAPI()
    try:
        available_secrets = await modal_api.list_secrets()
        results = {}

        for secret in secrets:
            results[secret] = secret in available_secrets

        return results
    finally:
        await modal_api.close()


async def list_modal_deployments() -> list[dict[str, Any]]:
    """List all Modal deployments with enhanced metadata.

    Returns:
        List of deployment information dictionaries
    """
    modal_api = ModalAPI()
    try:
        return await modal_api.list_deployments()
    finally:
        await modal_api.close()


async def kill_modal_deployment(app_name: str) -> bool:
    """Kill a specific Modal deployment.

    Args:
        app_name: Name of the app to kill

    Returns:
        True if successful, False otherwise
    """
    modal_api = ModalAPI()
    try:
        return await modal_api.kill_deployment(app_name)
    finally:
        await modal_api.close()


async def get_deployment_logs(app_name: str, lines: int = 100) -> str:
    """Get logs for a specific deployment.

    Args:
        app_name: Name of the app
        lines: Number of log lines to retrieve

    Returns:
        Log content as string
    """
    modal_api = ModalAPI()
    try:
        return await modal_api.get_app_logs(app_name, lines)
    finally:
        await modal_api.close()


def _suggest_deployment_mode(ml_libraries: list[str], jupyter_libraries: list[str]) -> str:
    """Suggest the best deployment mode based on detected libraries."""
    if jupyter_libraries:
        return "gra_jupy"
    if ml_libraries:
        return "optimized"
    return "minimum"


def get_modal_status() -> dict[str, Any]:
    """Get comprehensive Modal deployment status with enhanced information.

    Returns:
        dict: Status information including authentication, deployments, and metadata
    """
    try:
        deployer = ModalDeployer(Path("dummy"), "minimum")

        # Check authentication
        auth_status = uvloop.run(deployer.check_modal_auth_async())

        if not auth_status:
            return {"authenticated": False, "deployments": [], "secrets": [], "error": "Not authenticated with Modal"}

        # Get enhanced deployment information
        deployments = uvloop.run(list_modal_deployments())

        # Get secrets information
        try:
            modal_api = ModalAPI()
            secrets = uvloop.run(modal_api.list_secrets())
            uvloop.run(modal_api.close())
        except Exception as e:
            logger.warning(f"Failed to get secrets: {e}")
            secrets = []

        # Calculate statistics
        active_deployments = [d for d in deployments if d.get("status") == "running"]

        return {
            "authenticated": True,
            "deployments": deployments,
            "secrets": secrets,
            "total_deployments": len(deployments),
            "active_deployments": len(active_deployments),
            "available_secrets": len(secrets),
            "deployment_summary": {
                "total": len(deployments),
                "active": len(active_deployments),
                "inactive": len(deployments) - len(active_deployments),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get Modal status: {e}")
        return {"authenticated": False, "deployments": [], "secrets": [], "error": str(e)}


def deploy_with_validation(
    app_file: Path,
    config: DeploymentConfig | None = None,
    mode: str = "minimum",
    br_huehuehue: bool = False,
    timeout_minutes: int = 60,
    dry_run: bool = False,
) -> DeploymentResult:
    """Deploy with comprehensive validation and enhanced configuration support.

    Args:
        app_file: Path to the Gradio app file
        config: Optional deployment configuration
        mode: Deployment mode (minimum, optimized, gra_jupy, marimo) - used if config not provided
        br_huehuehue: Brazilian mode
        timeout_minutes: Deployment timeout in minutes - used if config not provided
        dry_run: Generate files without deploying

    Returns:
        DeploymentResult: Comprehensive deployment result
    """
    try:
        # Create deployment configuration if not provided
        if config is None:
            config = create_deployment_config(mode=mode, timeout_minutes=timeout_minutes, app_name=app_file.stem)

        # Validate deployment configuration
        config_validation = validate_deployment_config(config)
        if not config_validation["valid"]:
            error_msg = f"Configuration validation failed: {'; '.join(config_validation['issues'])}"
            rprint(f"[red]❌ {error_msg}[/red]")
            return DeploymentResult(success=False, error=error_msg, config=config)

        # Show configuration warnings
        if config_validation.get("warnings"):
            rprint("[yellow]⚠️  Configuration warnings:[/yellow]")
            for warning in config_validation["warnings"]:
                rprint(f"  • {warning}")

        # Validate app file
        validation = validate_app_file(app_file)
        if not validation["valid"]:
            error_msg = f"App validation failed: {validation['error']}"
            rprint(f"[red]❌ {error_msg}[/red]")
            if validation.get("recommendations"):
                rprint("[yellow]💡 Recommendations:[/yellow]")
                for rec in validation["recommendations"]:
                    rprint(f"  • {rec}")
            return DeploymentResult(success=False, error=error_msg, config=config)

        # Show validation warnings
        if validation.get("warnings"):
            rprint("[yellow]⚠️  App warnings:[/yellow]")
            for warning in validation["warnings"]:
                rprint(f"  • {warning}")

        # Create deployer with enhanced configuration
        deployer = ModalDeployer(app_file, config.mode, br_huehuehue, config)

        # Run deployment
        if dry_run:
            rprint(f"[{MODAL_GREEN}]🏃 Dry run mode - generating enhanced deployment files[/{MODAL_GREEN}]")
            try:
                deployment_file = uvloop.run(deployer.create_modal_deployment_async(app_file, config))
                rprint(f"[{MODAL_GREEN}]✅ Enhanced deployment file created: {deployment_file}[/{MODAL_GREEN}]")
                rprint(f"[{MODAL_GREEN}]💡 To deploy: modal deploy {deployment_file}[/{MODAL_GREEN}]")

                # Show configuration summary
                rprint(f"[{MODAL_LIGHT_GREEN}]⚙️ Configuration summary:[/{MODAL_LIGHT_GREEN}]")
                rprint(f"  • Mode: {config.mode}")
                rprint(f"  • GPU: {config.gpu_type or 'CPU only'}")
                rprint(f"  • Containers: {config.min_containers}-{config.max_containers}")
                rprint(f"  • Timeout: {config.timeout_minutes} minutes")
                if config.environment_variables:
                    rprint(f"  • Environment variables: {len(config.environment_variables)}")
                if config.secrets:
                    rprint(f"  • Secrets: {len(config.secrets)}")

                return DeploymentResult(success=True, deployment_file=deployment_file, config=config)
            except Exception as e:
                logger.error(f"Dry run failed: {e}")
                return DeploymentResult(success=False, error=f"Dry run failed: {e}", config=config)
        else:
            # Full enhanced deployment
            result = uvloop.run(deployer.deploy(config))
            return result

    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        rprint(f"[red]❌ Deployment failed: {e}[/red]")
        return DeploymentResult(success=False, error=str(e), config=config)
