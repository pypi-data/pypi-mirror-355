"""Enhanced Modal Dashboard with Easy Authentication and Template Generation.

This dashboard provides a complete Modal experience for beginners:
- Super easy OAuth-style authentication
- Advanced template generation wizard
- Deployment monitoring and management
- No CLI knowledge required!
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gradio as gr
from loguru import logger
from rich import print as rprint

from modal_for_noobs.cli_helpers.common import MODAL_GREEN, MODAL_LIGHT_GREEN
from modal_for_noobs.easy_auth import easy_modal_auth
from modal_for_noobs.template_generator import (
    RemoteFunctionConfig,
    TemplateConfig,
    TemplateGenerator,
    generate_from_wizard_input,
)


class EnhancedModalDashboard:
    """Enhanced dashboard with all features integrated."""

    def __init__(self):
        """Initialize the enhanced dashboard."""
        self.template_generator = TemplateGenerator()
        self.is_authenticated = False
        self.current_workspace = None

    def create_complete_interface(self) -> gr.Blocks:
        """Create the complete dashboard interface.

        Returns:
            Gradio Blocks interface with all features
        """
        # Custom CSS for better styling
        custom_css = """
        .auth-status {
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            border: 2px solid;
        }
        .auth-success {
            background-color: #ecfdf5;
            border-color: #10b981;
            color: #047857;
        }
        .auth-pending {
            background-color: #f0f9ff;
            border-color: #3b82f6;
            color: #1d4ed8;
        }
        .auth-error {
            background-color: #fef2f2;
            border-color: #ef4444;
            color: #dc2626;
        }
        .wizard-step {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin: 8px 0;
            font-weight: bold;
        }
        .deployment-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            background: #f9fafb;
        }
        """

        with gr.Blocks(
            title="Modal for Noobs - Complete Dashboard",
            css=custom_css,
            theme=gr.themes.Soft(primary_hue="blue", secondary_hue="gray", neutral_hue="gray"),
        ) as dashboard:
            # Header
            gr.HTML("""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 2.5em;">🚀 Modal for Noobs</h1>
                <p style="margin: 10px 0 0 0; font-size: 1.2em;">Deploy to Modal in minutes, not hours!</p>
            </div>
            """)

            # Global state
            auth_state = gr.State(value={"authenticated": False, "workspace": None})

            with gr.Tabs() as main_tabs:
                # Tab 1: Easy Authentication
                with gr.Tab("🔐 Connect to Modal"):
                    gr.Markdown("## Welcome! Let's get you connected to Modal")
                    gr.Markdown(
                        "Modal is a powerful cloud platform for running Python code. "
                        "We'll help you connect in just one click - no API keys needed!"
                    )

                    # Easy auth interface
                    easy_auth_interface = easy_modal_auth.create_easy_auth_interface()

                # Tab 2: App Generator
                with gr.Tab("🎯 Generate Your App", interactive=False) as generate_tab:
                    with gr.Column():
                        # Auth check header
                        auth_check = gr.HTML(value=self._get_auth_check_html(False), elem_id="auth-check-generate")

                        # Generator interface
                        with gr.Column() as generator_section:
                            gr.Markdown("## 🧙‍♂️ App Generation Wizard")
                            gr.Markdown(
                                "Create a powerful Modal deployment for your Python app with "
                                "our step-by-step wizard. No experience required!"
                            )

                            # File upload
                            app_file_upload = gr.File(label="📁 Upload Your Python App", file_types=[".py"], type="filepath", scale=2)

                            # or paste code
                            gr.Markdown("**Or paste your code here:**")
                            code_input = gr.Code(
                                label="Python Code",
                                language="python",
                                placeholder="# Paste your Gradio app code here...\nimport gradio as gr\n\ndef greet(name):\n    return f'Hello {name}!'\n\ndemo = gr.Interface(fn=greet, inputs='text', outputs='text')\ndemo.launch()",
                                lines=10,
                            )

                            # Wizard sections
                            with gr.Accordion("⚙️ Configuration Wizard", open=True):
                                # Step 1: Basic Settings
                                with gr.Group():
                                    gr.HTML('<div class="wizard-step">Step 1: Basic Settings</div>')
                                    with gr.Row():
                                        app_name_input = gr.Textbox(label="App Name", placeholder="my-awesome-app", scale=2)
                                        deployment_mode = gr.Dropdown(
                                            label="Deployment Mode",
                                            choices=[
                                                ("🌱 Minimum - Fast & cheap", "minimum"),
                                                ("⚡ Optimized - GPU + ML", "optimized"),
                                                ("📓 Marimo - Reactive notebooks", "marimo"),
                                                ("🪐 Gradio+Jupyter - Classic notebooks", "gradio-jupyter"),
                                            ],
                                            value="minimum",
                                            scale=2,
                                        )

                                # Step 2: Advanced Features
                                with gr.Group():
                                    gr.HTML('<div class="wizard-step">Step 2: Features (Optional)</div>')
                                    with gr.Row():
                                        enable_gpu = gr.Checkbox(label="🚀 Enable GPU", value=False)
                                        gpu_type = gr.Dropdown(
                                            label="GPU Type",
                                            choices=["any", "T4", "L4", "A10G", "A100", "H100"],
                                            value="any",
                                            visible=False,
                                        )
                                        enable_storage = gr.Checkbox(label="💾 Persistent Storage", value=False)

                                    with gr.Row():
                                        timeout_minutes = gr.Slider(label="⏱️ Timeout (minutes)", minimum=5, maximum=120, value=60, step=5)
                                        max_containers = gr.Slider(label="📈 Max Containers", minimum=1, maximum=50, value=10, step=1)

                                # Step 3: Dependencies
                                with gr.Group():
                                    gr.HTML('<div class="wizard-step">Step 3: Dependencies (Optional)</div>')
                                    requirements_upload = gr.File(label="📦 Upload requirements.txt", file_types=[".txt"], type="filepath")
                                    extra_packages = gr.Textbox(
                                        label="Extra Python Packages",
                                        placeholder="numpy, pandas, scikit-learn",
                                        info="Comma-separated list of additional packages",
                                    )

                            # Generate button
                            generate_btn = gr.Button("🚀 Generate Deployment", variant="primary", size="lg", scale=1)

                            # Output
                            generation_output = gr.Code(label="Generated Deployment Code", language="python", lines=20, visible=False)

                            download_btn = gr.DownloadButton(label="📥 Download Deployment File", visible=False)

                            deploy_btn = gr.Button("🚀 Deploy to Modal", variant="primary", visible=False)

                # Tab 3: Monitor Deployments
                with gr.Tab("📊 Monitor & Manage", interactive=False) as monitor_tab:
                    with gr.Column():
                        # Auth check header
                        auth_check_monitor = gr.HTML(value=self._get_auth_check_html(False), elem_id="auth-check-monitor")

                        # Monitoring interface
                        with gr.Column() as monitoring_section:
                            gr.Markdown("## 📊 Deployment Monitoring")

                            with gr.Row():
                                refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
                                stop_selected_btn = gr.Button("🛑 Stop Selected", variant="secondary")

                            # Deployments table
                            deployments_df = gr.Dataframe(
                                headers=["App Name", "Status", "URL", "Created", "GPU", "Cost"],
                                datatype=["str", "str", "str", "str", "str", "str"],
                                col_count=(6, "fixed"),
                                label="Your Deployments",
                            )

                            # Selected deployment details
                            with gr.Row():
                                with gr.Column():
                                    selected_app = gr.Dropdown(label="Select App for Details", choices=[], interactive=True)

                                with gr.Column():
                                    view_logs_btn = gr.Button("📝 View Logs")
                                    get_info_btn = gr.Button("ℹ️ Get Info")

                            # Logs output
                            logs_output = gr.Code(label="Application Logs", language="bash", lines=15, visible=False)

                # Tab 4: Help & Tutorials
                with gr.Tab("❓ Help & Tutorials"):
                    gr.Markdown("## 🎓 Getting Started with Modal")

                    with gr.Accordion("📚 Quick Start Guide", open=True):
                        gr.Markdown("""
                        ### 1. Connect to Modal
                        - Click the "Connect to Modal" tab
                        - Click "Connect to Modal (One Click!)"
                        - Authorize in the browser tab that opens
                        
                        ### 2. Generate Your App
                        - Go to the "Generate Your App" tab
                        - Upload your Python file or paste your code
                        - Configure your deployment settings
                        - Click "Generate Deployment"
                        
                        ### 3. Deploy and Monitor
                        - Review the generated code
                        - Click "Deploy to Modal"
                        - Monitor in the "Monitor & Manage" tab
                        """)

                    with gr.Accordion("🎯 Examples"):
                        gr.Markdown("""
                        ### Simple Gradio App
                        ```python
                        import gradio as gr
                        
                        def greet(name):
                            return f"Hello {name}!"
                        
                        demo = gr.Interface(fn=greet, inputs="text", outputs="text")
                        demo.launch()
                        ```
                        
                        ### ML Model with GPU
                        ```python
                        import gradio as gr
                        import torch
                        
                        def predict(text):
                            # Your ML model here
                            return f"Processed: {text}"
                        
                        demo = gr.Interface(fn=predict, inputs="text", outputs="text")
                        demo.launch()
                        ```
                        """)

                    with gr.Accordion("🔧 Troubleshooting"):
                        gr.Markdown("""
                        ### Common Issues
                        
                        **Authentication problems:**
                        - Make sure you clicked "Authorize" in the browser
                        - Try refreshing the page and connecting again
                        
                        **Deployment fails:**
                        - Check that your code has a `demo` variable
                        - Make sure all dependencies are included
                        - Try the "minimum" mode first
                        
                        **App won't start:**
                        - Check the logs in the monitoring tab
                        - Verify your code works locally first
                        """)

            # Event handlers
            def show_gpu_options(enable_gpu):
                return gr.update(visible=enable_gpu)

            def generate_deployment_code(
                file_path,
                code,
                app_name,
                mode,
                enable_gpu,
                gpu_type,
                enable_storage,
                timeout,
                max_containers,
                requirements_file,
                extra_packages,
            ):
                """Generate deployment code from wizard inputs."""
                try:
                    # Get source code
                    if file_path:
                        source_code = Path(file_path).read_text()
                        if not app_name:
                            app_name = Path(file_path).stem
                    elif code:
                        source_code = code
                        if not app_name:
                            app_name = "my-gradio-app"
                    else:
                        return None, False, False, "❌ Please provide either a file or code!"

                    # Parse extra packages
                    python_deps = []
                    if extra_packages:
                        python_deps = [pkg.strip() for pkg in extra_packages.split(",") if pkg.strip()]

                    # Generate deployment
                    deployment_code = generate_from_wizard_input(
                        app_name=app_name,
                        deployment_mode=mode,
                        original_code=source_code,
                        provision_nfs=enable_storage,
                        gpu_type=gpu_type if enable_gpu else None,
                        python_dependencies=python_deps,
                        requirements_file=Path(requirements_file) if requirements_file else None,
                    )

                    # Create download file
                    output_file = f"modal_{app_name}.py"
                    with open(output_file, "w") as f:
                        f.write(deployment_code)

                    return (
                        gr.update(value=deployment_code, visible=True),
                        gr.update(value=output_file, visible=True),
                        gr.update(visible=True),
                        "✅ Deployment code generated successfully!",
                    )

                except Exception as e:
                    return (None, False, False, f"❌ Generation failed: {str(e)}")

            # Connect events
            enable_gpu.change(fn=show_gpu_options, inputs=enable_gpu, outputs=gpu_type)

            generate_btn.click(
                fn=generate_deployment_code,
                inputs=[
                    app_file_upload,
                    code_input,
                    app_name_input,
                    deployment_mode,
                    enable_gpu,
                    gpu_type,
                    enable_storage,
                    timeout_minutes,
                    max_containers,
                    requirements_upload,
                    extra_packages,
                ],
                outputs=[generation_output, download_btn, deploy_btn, auth_check],
            )

            # Tab activation (require auth for generate and monitor tabs)
            def check_auth_and_enable_tab(tab_name):
                # In a real implementation, check actual auth status
                # For now, return enabled
                return gr.update(interactive=True)

            # Auto-enable tabs when authenticated (simplified for demo)
            dashboard.load(fn=lambda: (gr.update(interactive=True), gr.update(interactive=True)), outputs=[generate_tab, monitor_tab])

        return dashboard

    def _get_auth_check_html(self, is_authenticated: bool, workspace: str = None) -> str:
        """Get authentication status HTML."""
        if is_authenticated:
            return f"""
            <div class="auth-status auth-success">
                <span style="font-size: 20px;">✅</span>
                <strong>Connected to Modal</strong>
                {f" (Workspace: {workspace})" if workspace else ""}
            </div>
            """
        else:
            return """
            <div class="auth-status auth-error">
                <span style="font-size: 20px;">❌</span>
                <strong>Please connect to Modal first</strong>
                <br>Go to the "Connect to Modal" tab to get started
            </div>
            """


def launch_enhanced_dashboard(port: int = 7860, share: bool = False):
    """Launch the enhanced Modal dashboard.

    Args:
        port: Port to run the dashboard on
        share: Whether to create a public share link
    """
    dashboard = EnhancedModalDashboard()
    interface = dashboard.create_complete_interface()

    rprint(f"[{MODAL_GREEN}]🚀 Launching Enhanced Modal Dashboard...[/{MODAL_GREEN}]")
    rprint(f"[{MODAL_LIGHT_GREEN}]📊 Dashboard will be available at: http://localhost:{port}[/{MODAL_LIGHT_GREEN}]")
    rprint(f"[{MODAL_LIGHT_GREEN}]✨ Features: Easy auth, template generation, monitoring, and more![/{MODAL_LIGHT_GREEN}]")

    interface.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=share,
        quiet=False,
        show_error=True,
        debug=False,
        strict_cors=False,  # Allow localhost, HuggingFace, and Modal cross-origin requests
    )


if __name__ == "__main__":
    # For testing
    launch_enhanced_dashboard()
