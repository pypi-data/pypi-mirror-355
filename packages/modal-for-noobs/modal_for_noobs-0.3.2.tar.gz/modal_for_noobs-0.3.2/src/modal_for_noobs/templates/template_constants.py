"""Template constants for modal-for-noobs deployment templates.

This module contains pre-built template components that can be safely assembled
without f-string conflicts or nested quote issues.
"""

# Basic imports section
MODAL_IMPORTS = """import modal
import sys
import os
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import gradio as gr
from gradio.routes import mount_gradio_app
from loguru import logger"""

# Dashboard imports
DASHBOARD_IMPORTS = """# Import dashboard components
sys.path.append(str(Path(__file__).parent))
from dashboard import create_dashboard_interface, create_dashboard_api, dashboard_state, DeploymentInfo"""

# Marimo imports
MARIMO_IMPORTS = """import marimo as mo
import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt"""

# Standard Gradio interface detection
GRADIO_DETECTION = """# Detect Gradio Interface
demo = None
interface_names = ['demo', 'app', 'interface', 'iface']

for name in interface_names:
    if name in globals() and hasattr(globals()[name], 'launch'):
        demo = globals()[name]
        logger.info("Found Gradio interface: " + name)
        break

if demo is None:
    for var_name, var_value in globals().items():
        if hasattr(var_value, 'queue') and hasattr(var_value, 'launch'):
            demo = var_value
            logger.info("Found Gradio interface through scanning: " + var_name)
            break

if demo is None:
    logger.error("No Gradio interface found")
    raise ValueError("Could not find Gradio interface")"""

# Marimo notebook content - using safe string concatenation
MARIMO_NOTEBOOK_HEADER = '''import marimo

__generated_with = "0.1.0"
app = marimo.App()

@app.cell
def __():
    import marimo as mo
    return mo,

@app.cell
def __(mo):
    mo.md(r"""'''

MARIMO_NOTEBOOK_WELCOME = """# Welcome to Modal Marimo! 🎉

This Marimo notebook is running alongside your Gradio app on Modal.

Marimo provides:
- **Reactive notebooks** - cells automatically re-run when dependencies change
- **Pure Python** - notebooks are just Python files
- **Interactive widgets** - build UIs with Python
- **GPU acceleration** - full ML/AI support

Your Gradio app is available at the [root URL](/)."""

MARIMO_NOTEBOOK_FOOTER = '''""")
    return

@app.cell
def __():
    import sys
    import torch
    import pandas as pd
    import numpy as np
    
    print("Python " + sys.version)
    print("PyTorch " + torch.__version__)
    print("CUDA available: " + str(torch.cuda.is_available()))
    
    if torch.cuda.is_available():
        print("GPU: " + torch.cuda.get_device_name(0))
    return np, pd, sys, torch

@app.cell
def __(mo):
    mo.md("## Interactive Example")
    slider = mo.ui.slider(1, 10, value=5, label="Select a value")
    return slider,

@app.cell
def __(mo, slider):
    mo.md("You selected: **" + str(slider.value) + "**")
    
    # Create a simple plot
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots()
    ax.bar(range(slider.value), range(slider.value))
    ax.set_title("Bar chart with " + str(slider.value) + " bars")
    plt.tight_layout()
    return ax, fig, plt

if __name__ == "__main__":
    app.run()'''

# Marimo server startup function
MARIMO_SERVER_FUNCTION = '''async def start_marimo_server():
    """Start Marimo server in the background."""
    # Create workspace directory
    workspace_dir = Path("/workspace")
    workspace_dir.mkdir(exist_ok=True)
    
    # Create a sample Marimo notebook
    sample_notebook = workspace_dir / "welcome.py"
    if not sample_notebook.exists():
        notebook_content = MARIMO_NOTEBOOK_HEADER + MARIMO_NOTEBOOK_WELCOME + MARIMO_NOTEBOOK_FOOTER
        sample_notebook.write_text(notebook_content)
    
    # Start Marimo server
    logger.info("Starting Marimo server on port 2718")
    process = await asyncio.create_subprocess_exec(
        "marimo", "run",
        "--host", "0.0.0.0",
        "--port", "2718",
        "--no-browser",
        str(workspace_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Give it time to start
    await asyncio.sleep(3)
    logger.info("Marimo server started")
    
    return process'''

# Standard FastAPI setup
FASTAPI_BASIC_SETUP = """fastapi_app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)"""

# GPU detection code
GPU_DETECTION = '''# Check GPU availability
import torch
gpu_available = torch.cuda.is_available()
gpu_name = torch.cuda.get_device_name(0) if gpu_available else "None"'''

# Deployment info initialization
DEPLOYMENT_INFO_INIT = """# Initialize deployment info
deployment_info = DeploymentInfo(
    app_name=APP_NAME,
    deployment_mode=DEPLOYMENT_MODE,
    deployment_time=datetime.now().isoformat(),
    modal_version=modal.__version__,
    python_version=str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro),
    gpu_enabled=gpu_available,
    timeout_seconds=TIMEOUT_SECONDS,
    max_containers=MAX_CONTAINERS,
    environment={
        **{k: v for k, v in os.environ.items() if k.startswith("MODAL_")},
        "GPU_AVAILABLE": str(gpu_available),
        "GPU_NAME": gpu_name,
    }
)
dashboard_state.set_deployment_info(deployment_info)"""

# Marimo dashboard tab
MARIMO_DASHBOARD_TAB = '''# Marimo Tab (first for easy access)
with gr.Tab("📓 Marimo Notebooks"):
    gr.Markdown("### Interactive Marimo Notebook Environment")
    gr.Markdown("Access Marimo for reactive Python notebooks with GPU support.")
    
    with gr.Row():
        gr.Markdown("**Marimo is running on port 2718**")
        marimo_btn = gr.Button("🚀 Open Marimo", variant="primary", scale=2)
    
    gr.Markdown("""
    #### Why Marimo?
    - **Reactive notebooks** - Cells automatically update when dependencies change
    - **Pure Python files** - Version control friendly, no JSON
    - **Built-in UI components** - Create interactive apps with Python
    - **GPU acceleration** - Full PyTorch and ML support
    
    #### Features:
    - Pre-installed ML/AI packages
    - GPU support enabled
    - Interactive widgets and visualizations
    - Persistent workspace at `/workspace`
    
    #### Usage:
    1. Click the button above to open Marimo in a new tab
    2. Create reactive notebooks with `.py` extension
    3. Build interactive ML experiments
    """)
    
    # JavaScript to open Marimo in new tab
    marimo_btn.click(
        None,
        None,
        None,
        js="window.open('/marimo', '_blank')"
    )'''

# Marimo proxy endpoints
MARIMO_PROXY_ENDPOINTS = '''# Add Marimo proxy endpoint
@fastapi_app.get("/marimo")
@fastapi_app.get("/marimo/{path:path}")
async def marimo_proxy(path: str = ""):
    """Proxy requests to Marimo."""
    # Redirect to Marimo
    marimo_url = "http://localhost:2718/" + path
    return RedirectResponse(url=marimo_url)'''

# Queue configuration
DEMO_QUEUE_CONFIG = """# Configure demo queue
demo.queue(max_size=20)"""

# Dashboard module creation
DASHBOARD_MODULE_CREATION = """# Import dashboard module
dashboard_content = DASHBOARD_MODULE_TEMPLATE

# Write dashboard module
dashboard_path = Path(__file__).parent / "dashboard.py"
if not dashboard_path.exists():
    dashboard_path.write_text(dashboard_content)"""

# Standard app execution
APP_EXECUTION = """if __name__ == "__main__":
    app.run()"""

# Enhanced dashboard with monitoring
ENHANCED_DASHBOARD_CREATION = """# Create Dashboard
with gr.Blocks() as enhanced_dashboard:
    gr.Markdown("# 🚀 Modal Deployment Dashboard")
    gr.Markdown("Monitor and manage your Modal deployment")
    
    with gr.Tabs():
        # Original dashboard tabs
        dashboard_interface = create_dashboard_interface(demo)
        for tab in dashboard_interface.children:
            if hasattr(tab, 'children'):
                for child in tab.children:
                    child.render()
    
    gr.Markdown("---")
    gr.Markdown("🚀 Powered by [Modal](https://modal.com) | Generated by [modal-for-noobs](https://github.com/arthrod/modal-for-noobs)")"""

# Dashboard module template
DASHBOARD_MODULE_TEMPLATE = '''"""Dashboard module - embedded for deployment."""

import gradio as gr
import modal
import asyncio
import subprocess
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class DeploymentInfo:
    """Store deployment information."""
    app_name: str
    deployment_mode: str
    deployment_time: str
    modal_version: str
    python_version: str
    gpu_enabled: bool
    timeout_seconds: int
    max_containers: int
    environment: Dict[str, str]

class DashboardState:
    """Global state for dashboard."""
    
    def __init__(self):
        self.deployment_info: Optional[DeploymentInfo] = None
        self.logs: list = []
    
    def set_deployment_info(self, info: DeploymentInfo):
        self.deployment_info = info
    
    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > 100:  # Keep last 100 logs
            self.logs = self.logs[-100:]

dashboard_state = DashboardState()

def create_dashboard_interface(demo):
    """Create the dashboard interface."""
    
    def get_deployment_info():
        if dashboard_state.deployment_info:
            info = dashboard_state.deployment_info
            return f"""
            **App Name:** {info.app_name}
            **Mode:** {info.deployment_mode}
            **Deployed:** {info.deployment_time}
            **Modal Version:** {info.modal_version}
            **Python:** {info.python_version}
            **GPU Enabled:** {info.gpu_enabled}
            **Timeout:** {info.timeout_seconds}s
            **Max Containers:** {info.max_containers}
            """
        return "No deployment info available"
    
    def get_logs():
        return "\\n".join(dashboard_state.logs[-20:]) if dashboard_state.logs else "No logs available"
    
    with gr.Blocks() as dashboard:
        with gr.Tab("📊 Status"):
            gr.Markdown("### Deployment Information")
            deployment_info = gr.Textbox(
                value=get_deployment_info(),
                label="Deployment Details",
                lines=8,
                interactive=False
            )
            
            refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
            refresh_btn.click(
                lambda: get_deployment_info(),
                outputs=deployment_info
            )
        
        with gr.Tab("📝 Logs"):
            gr.Markdown("### Application Logs")
            logs_display = gr.Textbox(
                value=get_logs(),
                label="Recent Logs",
                lines=15,
                interactive=False
            )
            
            refresh_logs_btn = gr.Button("🔄 Refresh Logs", variant="secondary")
            refresh_logs_btn.click(
                lambda: get_logs(),
                outputs=logs_display
            )
    
    return dashboard

def create_dashboard_api(fastapi_app):
    """Add dashboard API endpoints."""
    
    @fastapi_app.get("/api/deployment-info")
    async def get_deployment_info_api():
        if dashboard_state.deployment_info:
            return dashboard_state.deployment_info.__dict__
        return {"error": "No deployment info available"}
    
    @fastapi_app.get("/api/logs")
    async def get_logs_api():
        return {"logs": dashboard_state.logs}
    
    return fastapi_app'''


# Function to build complete templates
def build_template(mode: str, **kwargs) -> str:
    """Build a complete template from constants."""
    # Common header
    header = f'''# 🚀 Modal Deployment Script ({mode.title()} Configuration)
# Generated by modal-for-noobs - https://github.com/arthrod/modal-for-noobs
# Deployment Mode: {mode}
# Features: {kwargs.get("features", "Gradio app with monitoring")}

{MODAL_IMPORTS}

{DASHBOARD_IMPORTS if kwargs.get("dashboard", True) else ""}

# Configuration constants
APP_NAME = "{kwargs.get("app_name", "modal-app")}"
APP_TITLE = "{kwargs.get("app_title", "Modal App")}"
APP_DESCRIPTION = "{kwargs.get("app_description", "Deployed with modal-for-noobs")}"
DEPLOYMENT_MODE = "{mode}"
TIMEOUT_SECONDS = {kwargs.get("timeout_seconds", 300)}
MAX_CONTAINERS = {kwargs.get("max_containers", 1)}

# Create Modal App
app = modal.App(APP_NAME)

# Container Image Configuration
{kwargs.get("image_config", 'image = modal.Image.debian_slim().pip_install("gradio")')}

# Original Application Code
{kwargs.get("original_code", "# Your application code here")}'''

    return header


# Template assembly functions
def get_marimo_template_parts():
    """Get all parts needed for marimo template assembly."""
    return {
        "imports": MODAL_IMPORTS + "\n" + DASHBOARD_IMPORTS,
        "marimo_imports": MARIMO_IMPORTS,
        "marimo_server": MARIMO_SERVER_FUNCTION,
        "gradio_detection": GRADIO_DETECTION,
        "gpu_detection": GPU_DETECTION,
        "deployment_info": DEPLOYMENT_INFO_INIT,
        "marimo_tab": MARIMO_DASHBOARD_TAB,
        "marimo_proxy": MARIMO_PROXY_ENDPOINTS,
        "dashboard_creation": ENHANCED_DASHBOARD_CREATION,
        "fastapi_setup": FASTAPI_BASIC_SETUP,
        "queue_config": DEMO_QUEUE_CONFIG,
        "dashboard_module": DASHBOARD_MODULE_TEMPLATE,
        "app_execution": APP_EXECUTION,
    }


def get_basic_template_parts():
    """Get all parts needed for basic template assembly."""
    return {
        "imports": MODAL_IMPORTS,
        "gradio_detection": GRADIO_DETECTION,
        "fastapi_setup": FASTAPI_BASIC_SETUP,
        "queue_config": DEMO_QUEUE_CONFIG,
        "app_execution": APP_EXECUTION,
    }
