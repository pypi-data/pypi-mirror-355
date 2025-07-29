"""Core Gradio components for Modal deployment.

This module provides reusable UI components for Modal deployment interfaces,
including deployment buttons, status monitors, and example explorers.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import gradio as gr
from loguru import logger

# Import our existing modules
from modal_for_noobs.cli_helpers.common import MODAL_BLACK, MODAL_DARK_GREEN, MODAL_GREEN, MODAL_LIGHT_GREEN
from modal_for_noobs.github_api import GitHubAPI


class ModalDeployButton(gr.HTML):
    """Beautiful one-click Modal deployment button for Gradio apps."""

    def __init__(
        self,
        app_file: str | Path,
        mode: str = "optimized",
        timeout_minutes: int = 60,
        auto_auth: bool = True,
        requirements_path: str | Path | None = None,
        test_deploy: bool = False,
        **kwargs,
    ):
        """Initialize Modal deployment button.

        Args:
            app_file: Path to the Gradio app file to deploy
            mode: Deployment mode (minimum, optimized, gradio-jupyter)
            timeout_minutes: Auto-kill timeout in minutes
            auto_auth: Automatically handle Modal authentication
            requirements_path: Path to requirements.txt file
            test_deploy: Deploy with immediate kill for testing
        """
        self.app_file = Path(app_file)
        self.mode = mode
        self.timeout_minutes = timeout_minutes
        self.auto_auth = auto_auth
        self.requirements_path = Path(requirements_path) if requirements_path else None
        self.test_deploy = test_deploy

        # Create beautiful Modal-themed deploy button
        button_html = self._create_deploy_button_html()
        super().__init__(value=button_html, **kwargs)

        # Set up deployment handler
        self._setup_deployment_handler()

    def _create_deploy_button_html(self) -> str:
        """Create beautiful HTML for the deploy button using Modal colors."""
        modal_green = MODAL_GREEN
        modal_light_green = MODAL_LIGHT_GREEN
        modal_black = MODAL_BLACK

        return f"""
        <div class="modal-deploy-container">
            <style>
                .modal-deploy-container {{
                    margin: 20px 0;
                    text-align: center;
                }}

                .modal-deploy-button {{
                    background: linear-gradient(135deg, {modal_green} 0%, {modal_light_green} 100%);
                    border: none;
                    color: {modal_black};
                    font-weight: bold;
                    border-radius: 12px;
                    padding: 16px 32px;
                    font-size: 18px;
                    cursor: pointer;
                    box-shadow: 0 4px 15px rgba(127, 238, 100, 0.4);
                    transition: all 0.3s ease;
                    text-decoration: none;
                    display: inline-block;
                    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                }}

                .modal-deploy-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(127, 238, 100, 0.6);
                    background: linear-gradient(135deg, {modal_light_green} 0%, {modal_green} 100%);
                }}

                .modal-deploy-status {{
                    margin-top: 15px;
                    padding: 10px;
                    border-radius: 8px;
                    background: rgba(127, 238, 100, 0.1);
                    border: 1px solid rgba(127, 238, 100, 0.3);
                    font-family: monospace;
                    font-size: 14px;
                }}
            </style>

            <button class="modal-deploy-button" onclick="deployToModal()">
                🚀 Deploy to Modal ({self.mode.upper()})
            </button>

            <div id="modal-deploy-status" class="modal-deploy-status" style="display: none;">
                📝 Ready to deploy...
            </div>

            <script>
                async function deployToModal() {{
                    const button = document.querySelector('.modal-deploy-button');
                    const status = document.getElementById('modal-deploy-status');

                    button.disabled = true;
                    button.innerHTML = '🚀 Deploying...';
                    status.style.display = 'block';
                    status.innerHTML = '📡 Starting deployment process...';

                    try {{
                        // Trigger deployment via Gradio
                        if (window.gradio_app && window.gradio_app.trigger_deployment) {{
                            await window.gradio_app.trigger_deployment();
                        }} else {{
                            status.innerHTML = '⚠️ Deployment handler not available';
                        }}
                    }} catch (error) {{
                        status.innerHTML = '❌ Deployment failed: ' + error.message;
                        button.disabled = false;
                        button.innerHTML = '🚀 Deploy to Modal ({self.mode.upper()})';
                    }}
                }}
            </script>
        </div>
        """

    def _setup_deployment_handler(self):
        """Set up the deployment event handler."""
        # This would be connected to the actual deployment logic
        # Integration with existing modal_deploy.py functionality
        pass


class ModalExplorer(gr.Blocks):
    """Interactive Modal examples explorer component."""

    def __init__(
        self, github_repo: str = "modal-labs/modal-examples", auto_refresh: bool = True, show_deploy_button: bool = True, **kwargs
    ):
        """Initialize Modal examples explorer.

        Args:
            github_repo: GitHub repository to explore
            auto_refresh: Automatically refresh content
            show_deploy_button: Show deployment buttons for examples
        """
        self.github_repo = github_repo
        self.auto_refresh = auto_refresh
        self.show_deploy_button = show_deploy_button

        # Initialize GitHub API using our existing implementation
        self.github_api = GitHubAPI(repo=github_repo)

        super().__init__(**kwargs)

        with self:
            self._create_explorer_interface()

    def _create_explorer_interface(self):
        """Create the explorer interface."""
        # Header with Modal styling
        gr.Markdown(f"""
        # 📁💚 Modal Examples Explorer 💚📁
        ### Explore {self.github_repo} in real-time!
        """)

        with gr.Row():
            with gr.Column(scale=1):
                # Folder selection
                self.folder_dropdown = gr.Dropdown(
                    label="📂 Select Folder", choices=["🔄 Loading..."], value="🔄 Loading...", interactive=True
                )

                # Python file selection
                self.file_dropdown = gr.Dropdown(
                    label="🐍 Select Python File", choices=["📝 Choose folder first"], value="📝 Choose folder first", interactive=True
                )

                if self.show_deploy_button:
                    self.deploy_button = gr.Button("🚀 Deploy This Example", variant="primary")

            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("📚 README"):
                        self.readme_display = gr.Markdown("📝 Select a folder to see its README")

                    with gr.TabItem("🐍 Code"):
                        self.code_display = gr.Code(value="🐍 Select a Python file to view its code", language="python")

        # Set up event handlers
        self._setup_event_handlers()

        # Load initial data
        self._load_folders()

    def _setup_event_handlers(self):
        """Set up event handlers for the interface."""
        # Folder change updates files and README
        self.folder_dropdown.change(
            fn=self._on_folder_change, inputs=self.folder_dropdown, outputs=[self.file_dropdown, self.readme_display]
        )

        # File change updates code display
        self.file_dropdown.change(fn=self._on_file_change, inputs=[self.folder_dropdown, self.file_dropdown], outputs=self.code_display)

    def _load_folders(self):
        """Load available folders from GitHub."""

        def sync_load_folders():
            try:
                # Use our existing GitHub API implementation
                folders = asyncio.run(self.github_api.get_all_folders())
                return folders
            except Exception as e:
                logger.error(f"Failed to load folders: {e}")
                return [{"name": "❌ Error loading folders"}]

        # Update dropdown with loaded folders
        folders = sync_load_folders()
        folder_choices = [f"📁 {folder['name']}" for folder in folders]

        self.folder_dropdown.choices = folder_choices
        if folder_choices:
            self.folder_dropdown.value = folder_choices[0]

    def _on_folder_change(self, folder_choice: str):
        """Handle folder selection change."""
        if not folder_choice or folder_choice.startswith("❌"):
            return (gr.Dropdown(choices=["📝 Invalid folder"], value="📝 Invalid folder"), "📝 Please select a valid folder")

        folder_name = folder_choice.replace("📁 ", "")

        # Load Python files
        def sync_load_files():
            try:
                return asyncio.run(self.github_api.get_python_files_in_folder(folder_name))
            except Exception as e:
                logger.error(f"Failed to load files: {e}")
                return []

        # Load README
        def sync_load_readme():
            try:
                return asyncio.run(self.github_api.get_readme_content(folder_name))
            except Exception as e:
                logger.error(f"Failed to load README: {e}")
                return f"❌ Error loading README: {e!s}"

        python_files = sync_load_files()
        readme_content = sync_load_readme()

        if python_files:
            file_choices = [f"🐍 {file['name']}" for file in python_files]
            file_dropdown_update = gr.Dropdown(choices=file_choices, value=file_choices[0] if file_choices else None)
        else:
            file_dropdown_update = gr.Dropdown(choices=["📝 No Python files found"], value="📝 No Python files found")

        return file_dropdown_update, readme_content

    def _on_file_change(self, folder_choice: str, file_choice: str):
        """Handle file selection change."""
        if not folder_choice or not file_choice or folder_choice.startswith(("❌", "🔄")) or file_choice.startswith(("📝", "❌")):
            return "🐍 Please select a valid folder and file"

        folder_name = folder_choice.replace("📁 ", "")
        file_name = file_choice.replace("🐍 ", "")
        file_path = f"{folder_name}/{file_name}"

        def sync_load_content():
            try:
                return asyncio.run(self.github_api.get_file_content(file_path))
            except Exception as e:
                logger.error(f"Failed to load file content: {e}")
                return f"❌ Error loading file: {e!s}"

        return sync_load_content()


class ModalStatusMonitor(gr.Blocks):
    """Real-time Modal deployment status monitor."""

    def __init__(self, refresh_interval: int = 5, show_logs: bool = True, show_costs: bool = True, **kwargs):
        """Initialize Modal status monitor.

        Args:
            refresh_interval: Refresh interval in seconds
            show_logs: Show deployment logs
            show_costs: Show cost information
        """
        self.refresh_interval = refresh_interval
        self.show_logs = show_logs
        self.show_costs = show_costs

        super().__init__(**kwargs)

        with self:
            self._create_monitor_interface()

    def _create_monitor_interface(self):
        """Create the monitoring interface."""
        gr.Markdown("""
        # 📊💚 Modal Status Monitor 💚📊
        ### Real-time deployment monitoring and management
        """)

        with gr.Row():
            with gr.Column():
                # Deployment list
                self.deployments_display = gr.Dataframe(
                    headers=["App", "Status", "URL", "Uptime", "Actions"], label="🚀 Active Deployments"
                )

                # Refresh button
                refresh_btn = gr.Button("🔄 Refresh", variant="secondary")

                # Bulk actions
                with gr.Row():
                    kill_all_btn = gr.Button("💀 Kill All", variant="stop")
                    restart_all_btn = gr.Button("♻️ Restart All", variant="primary")

            with gr.Column():
                if self.show_logs:
                    # Logs display
                    self.logs_display = gr.Code(value="📋 Select a deployment to view logs", label="📋 Deployment Logs", language="text")

                if self.show_costs:
                    # Cost information
                    self.costs_display = gr.Markdown("""
                    ### 💰 Cost Information
                    - **Current month:** $0.00
                    - **This deployment:** $0.00
                    - **Estimated daily:** $0.00
                    """)

        # Set up auto-refresh if enabled
        if self.refresh_interval > 0:
            # This would integrate with existing dashboard functionality
            pass


class ModalTheme(gr.Theme):
    """Beautiful Modal-themed Gradio theme with signature green colors.

    This is a legacy class for backwards compatibility.
    Use create_modal_theme() from themes.py instead.
    """

    def __init__(self):
        """Initialize Modal theme with beautiful green styling."""
        # Import here to avoid circular imports
        from .themes import create_modal_theme

        theme = create_modal_theme()
        super().__init__()

        # Copy all theme settings
        for key, value in theme.__dict__.items():
            setattr(self, key, value)
