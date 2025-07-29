"""Modal deployment template management.

This module handles loading and generating deployment templates based on
the selected mode (minimum, optimized, gradio-jupyter, marimo).
"""

import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


def get_image_config(deployment_mode: str, packages: list[str]) -> str:
    """Get Modal image configuration based on deployment mode.

    Args:
        deployment_mode: The deployment mode ("minimum", "optimized", "gra_jupy", "marimo").
        packages: List of packages to install.

    Returns:
        str: Modal image configuration string.
    """
    packages_str = ",\n    ".join([f'"{pkg}"' for pkg in packages])

    # For optimized and marimo modes, use GPU-optimized base image
    if deployment_mode in ["optimized", "marimo"]:
        return f"""image = (
    modal.Image.from_registry("nvidia/cuda:12.1-devel-ubuntu22.04", add_python="3.11")
    .pip_install(
        {packages_str}
    )
    .run_commands(
        # Install system dependencies for GPU acceleration
        "apt-get update && apt-get install -y git build-essential",
        # Verify GPU setup
        "nvidia-smi",
        # Optimize PyTorch for GPU
        "python -c 'import torch; print(f\\"PyTorch {{torch.__version__}} - CUDA available: {{torch.cuda.is_available()}}\\");'",
    )
)"""
    else:
        # Standard Debian slim for minimum and gradio-jupyter modes
        return f"""image = modal.Image.debian_slim(python_version="3.11").pip_install(
    {packages_str}
)"""


def load_template_module(template_name: str) -> Any:
    """Load a template module dynamically.

    Args:
        template_name: Name of the template (minimum, optimized, gradio-jupyter, marimo)

    Returns:
        The loaded module
    """
    template_dir = Path(__file__).parent / template_name
    template_file = template_dir / "deployment_template.py"

    if not template_file.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    spec = importlib.util.spec_from_file_location(f"{template_name}_template", template_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def load_dashboard_module() -> str:
    """Load the dashboard module content.

    Returns:
        str: The dashboard module content
    """
    dashboard_file = Path(__file__).parent / "dashboard.py"
    if not dashboard_file.exists():
        raise FileNotFoundError("Dashboard module not found")

    return dashboard_file.read_text()


def generate_modal_deployment(
    app_file: Path,
    original_code: str,
    deployment_mode: str = "minimum",
    timeout_seconds: int = 3600,
    scaledown_window: int = 1200,
    image_config: str = None,
) -> str:
    """Generate Modal deployment code using the new template system.

    Args:
        app_file: Path to the original Gradio app file
        original_code: Content of the original Gradio app
        deployment_mode: Deployment mode (minimum, optimized, gradio-jupyter, marimo)
        timeout_seconds: Function timeout in seconds
        scaledown_window: Scale down window in seconds

    Returns:
        str: Complete Modal deployment Python code
    """
    # Map old mode names to new ones
    mode_mapping = {"gra_jupy": "gradio-jupyter", "minimum": "minimum", "optimized": "optimized", "marimo": "marimo"}

    template_name = mode_mapping.get(deployment_mode, deployment_mode)

    # Load the template module
    try:
        template_module = load_template_module(template_name)
    except FileNotFoundError:
        # Fallback to old template system for backward compatibility
        return generate_modal_deployment_legacy(app_file, original_code, deployment_mode, timeout_seconds, scaledown_window)

    # If no image_config provided, generate one based on mode
    if image_config is None:
        from modal_for_noobs.config_loader import config_loader

        package_config = config_loader.load_base_packages()
        packages = package_config.get(deployment_mode, package_config.get("minimum", []))
        image_config = get_image_config(deployment_mode, packages)

    # Load dashboard module
    dashboard_content = load_dashboard_module()
    logger.debug(f"Dashboard content loaded: {len(dashboard_content)} characters")

    # Encode dashboard content to base64 to avoid quote conflicts
    import base64

    dashboard_content_b64 = base64.b64encode(dashboard_content.encode("utf-8")).decode("ascii")
    logger.debug(f"Dashboard content encoded to base64: {len(dashboard_content_b64)} characters")

    # Format the template
    template = template_module.TEMPLATE
    logger.debug(f"Template loaded: {len(template)} characters")

    try:
        formatted_code = template.format(
            app_name=f"modal-for-noobs-{app_file.stem}",
            original_code=original_code,
            timeout_seconds=timeout_seconds,
            scaledown_window=scaledown_window,
            dashboard_module=dashboard_content,
            dashboard_module_b64=dashboard_content_b64,
            image_config=image_config,
        )
        logger.debug("Template formatting successful")
    except Exception as e:
        logger.error(f"Template formatting failed: {e}")
        raise

    return formatted_code


def generate_modal_deployment_legacy(
    app_file: Path,
    original_code: str,
    deployment_mode: str = "minimum",
    timeout_seconds: int = 3600,
    scaledown_window: int = 1200,
) -> str:
    """Legacy deployment template generation for backward compatibility.

    This is the old template system that will be phased out.
    """
    from modal_for_noobs.config_loader import config_loader

    # Load packages for the deployment mode
    packages = config_loader.load_base_packages().get(deployment_mode, [])

    # Build image configuration
    packages_str = ",\n    ".join([f'"{pkg}"' for pkg in packages])
    image_config = f"""image = modal.Image.debian_slim(python_version="3.11").pip_install(
    {packages_str}
)"""

    metadata = {
        "app_name": f"modal-for-noobs-{app_file.stem}",
        "deployment_mode": deployment_mode,
        "timeout_seconds": timeout_seconds,
        "scaledown_window": scaledown_window,
        "gpu_line": '    gpu="any",' if deployment_mode in ["optimized", "gra_jupy"] else "",
    }

    return f'''# 🚀 Modal Deployment Script (Async Generated)
# Generated by modal-for-noobs - https://github.com/arthrod/modal-for-noobs
# Deployment Mode: {deployment_mode}
# Following Modal's technical design philosophy for high-performance cloud computing
# Timeout: {timeout_seconds}s | Scaledown: {scaledown_window}s

import modal
from fastapi import FastAPI
import gradio as gr
from gradio.routes import mount_gradio_app

# 🎯 Create Modal App with semantic naming
app = modal.App("{metadata["app_name"]}")

# 🐳 Container Image Configuration
# Optimized for {deployment_mode} workloads with performance-tuned dependencies
{image_config}

# 📦 Original Gradio Application Code
# Embedded for seamless execution in Modal's cloud infrastructure
{original_code}

# ⚡ Modal Function Configuration
# Engineered for scalability, performance, and reliability
@app.function(
    image=image,{metadata["gpu_line"]}
    min_containers=1,
    max_containers=1,  # Single container for session consistency and state management
    timeout={timeout_seconds},  # Configurable timeout for workload requirements
    scaledown_window={scaledown_window},  # Optimized scale-down for cost efficiency
)
@modal.concurrent(max_inputs=100)  # High concurrency for production-grade performance
@modal.asgi_app()
def deploy_gradio():
    """
    Deploy Gradio app with Modal's high-performance infrastructure.
    
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
    if 'demo' in globals():
        demo = globals()['demo']
    elif 'app' in globals() and hasattr(globals()['app'], 'queue'):
        demo = globals()['app']
    elif 'interface' in globals():
        demo = globals()['interface']
    elif 'iface' in globals():
        demo = globals()['iface']

    # Fallback detection: Comprehensive global scope scan
    if demo is None:
        for var_name, var_value in globals().items():
            if hasattr(var_value, 'queue') and hasattr(var_value, 'launch'):
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
        redoc_url="/redoc"  # Enable alternative API documentation
    )
    
    return mount_gradio_app(fastapi_app, demo, path="/")

# 🏃‍♂️ Direct execution support for local testing
if __name__ == "__main__":
    app.run()
'''
