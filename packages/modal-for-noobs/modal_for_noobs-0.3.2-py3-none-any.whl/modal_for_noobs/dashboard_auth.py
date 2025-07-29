"""Dashboard-based authentication for Modal - perfect for beginners!

This module provides a user-friendly authentication interface within
the Gradio dashboard, eliminating the need for CLI knowledge.
"""

import json
import os
import webbrowser
from pathlib import Path
from typing import Dict, Optional, Tuple

import gradio as gr
from loguru import logger

from modal_for_noobs.auth_manager import ModalAuthConfig, ModalAuthManager
from modal_for_noobs.cli_helpers.common import MODAL_GREEN


class DashboardAuthenticator:
    """Handles authentication directly from the dashboard UI."""

    def __init__(self):
        """Initialize the dashboard authenticator."""
        self.auth_manager = ModalAuthManager()
        self.auth_state = {
            "is_authenticated": False,
            "auth_config": None,
            "workspace": None,
        }

    def create_auth_interface(self) -> gr.Blocks:
        """Create the authentication interface for the dashboard.

        Returns:
            Gradio Blocks interface for authentication
        """
        with gr.Blocks() as auth_interface:
            gr.Markdown("# 🔐 Modal Authentication Setup")
            gr.Markdown("Welcome! Let's get you connected to Modal. It's super easy - just follow these simple steps:")

            # Check current auth status
            auth_status = gr.Textbox(label="Current Status", value=self._get_auth_status_message(), interactive=False, lines=2)

            with gr.Tabs() as auth_tabs:
                # Tab 1: Easy Setup
                with gr.Tab("🚀 Easy Setup"):
                    gr.Markdown("### Step 1: Get Your Modal Tokens")

                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown(
                                "1. Click the button to open Modal's token page\n"
                                "2. Sign up or log in to Modal (it's free!)\n"
                                "3. Copy your **Token ID** and **Token Secret**"
                            )
                        with gr.Column(scale=1):
                            open_modal_btn = gr.Button("🌐 Open Modal Tokens Page", variant="primary", scale=1)

                    gr.Markdown("### Step 2: Paste Your Tokens Here")

                    with gr.Row():
                        token_id_input = gr.Textbox(
                            label="Token ID (starts with 'ak-')", placeholder="ak-your-token-id-here", type="text", interactive=True
                        )
                        token_secret_input = gr.Textbox(
                            label="Token Secret (starts with 'as-')",
                            placeholder="as-your-token-secret-here",
                            type="password",
                            interactive=True,
                        )

                    workspace_input = gr.Textbox(label="Workspace Name (optional)", placeholder="your-workspace-name", interactive=True)

                    with gr.Row():
                        authenticate_btn = gr.Button("🔐 Authenticate", variant="primary", scale=1)
                        test_connection_btn = gr.Button("🧪 Test Connection", variant="secondary", scale=1)

                    auth_result = gr.Textbox(label="Result", interactive=False, lines=3)

                # Tab 2: File Upload Method
                with gr.Tab("📁 File Upload"):
                    gr.Markdown(
                        "### Alternative: Upload Your Modal Config File\n"
                        "If you already have Modal set up on another computer, "
                        "you can upload your config file."
                    )

                    config_file_upload = gr.File(label="Upload Modal Config File", file_types=[".toml", ".json"], type="filepath")

                    upload_result = gr.Textbox(label="Upload Result", interactive=False, lines=3)

                # Tab 3: Environment Setup Guide
                with gr.Tab("💻 Manual Setup"):
                    gr.Markdown(
                        """### For Advanced Users: Environment Variables
                        
                        If you prefer to set environment variables manually:
                        
                        **On Windows (Command Prompt):**
                        ```
                        set MODAL_TOKEN_ID=your-token-id
                        set MODAL_TOKEN_SECRET=your-token-secret
                        ```
                        
                        **On Windows (PowerShell):**
                        ```
                        $env:MODAL_TOKEN_ID="your-token-id"
                        $env:MODAL_TOKEN_SECRET="your-token-secret"
                        ```
                        
                        **On Mac/Linux:**
                        ```
                        export MODAL_TOKEN_ID=your-token-id
                        export MODAL_TOKEN_SECRET=your-token-secret
                        ```
                        
                        Then restart this dashboard for changes to take effect.
                        """
                    )

                    refresh_btn = gr.Button("🔄 Check Environment", variant="secondary")

                    env_check_result = gr.Textbox(label="Environment Check", interactive=False, lines=4)

            # Video Tutorial Section
            with gr.Accordion("📺 Video Tutorial", open=False):
                gr.HTML(
                    """
                    <div style="text-align: center; padding: 20px;">
                        <p>Need help? Watch this quick tutorial:</p>
                        <iframe 
                            width="560" 
                            height="315" 
                            src="https://www.youtube.com/embed/dQw4w9WgXcQ" 
                            title="Modal Authentication Tutorial" 
                            frameborder="0" 
                            allowfullscreen>
                        </iframe>
                    </div>
                    """
                )

            # Event handlers
            def open_modal_tokens_page():
                """Open Modal tokens page in browser."""
                webbrowser.open("https://modal.com/settings/tokens")
                return "✅ Opened Modal tokens page in your browser!"

            def authenticate_with_tokens(token_id: str, token_secret: str, workspace: str):
                """Authenticate using provided tokens."""
                if not token_id or not token_secret:
                    return "❌ Please provide both Token ID and Token Secret!", self._get_auth_status_message()

                # Create auth config
                auth_config = ModalAuthConfig(
                    token_id=token_id.strip(), token_secret=token_secret.strip(), workspace=workspace.strip() if workspace else None
                )

                # Validate
                is_valid, errors = auth_config.validate()
                if not is_valid:
                    error_msg = "❌ Validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
                    return error_msg, self._get_auth_status_message()

                # Test authentication
                if not self.auth_manager.test_authentication(auth_config):
                    return "❌ Authentication failed! Please check your tokens.", self._get_auth_status_message()

                # Apply to environment and save
                self.auth_manager.apply_auth_to_env(auth_config)
                self.auth_manager.save_auth(auth_config)

                # Update state
                self.auth_state["is_authenticated"] = True
                self.auth_state["auth_config"] = auth_config
                self.auth_state["workspace"] = workspace

                return "✅ Authentication successful! You're all set! 🎉", self._get_auth_status_message()

            def test_connection():
                """Test current Modal connection."""
                auth_config = self.auth_manager.get_auth_from_env()
                if not auth_config:
                    return "❌ No authentication found. Please authenticate first!"

                if self.auth_manager.test_authentication(auth_config):
                    return "✅ Connection successful! Modal is ready to use! 🚀"
                else:
                    return "❌ Connection failed. Please check your credentials."

            def handle_config_upload(filepath):
                """Handle config file upload."""
                if not filepath:
                    return "❌ No file uploaded!"

                try:
                    # Read and parse config file
                    config_path = Path(filepath)
                    if config_path.suffix == ".json":
                        config_data = json.loads(config_path.read_text())
                    else:
                        # Handle .toml files
                        import toml

                        config_data = toml.loads(config_path.read_text())

                    # Extract Modal credentials
                    token_id = config_data.get("token_id", "")
                    token_secret = config_data.get("token_secret", "")
                    workspace = config_data.get("workspace", "")

                    if not token_id or not token_secret:
                        return "❌ Config file doesn't contain valid Modal credentials!"

                    # Create and test auth config
                    auth_config = ModalAuthConfig(token_id=token_id, token_secret=token_secret, workspace=workspace if workspace else None)

                    if self.auth_manager.test_authentication(auth_config):
                        self.auth_manager.apply_auth_to_env(auth_config)
                        self.auth_manager.save_auth(auth_config)
                        return "✅ Config loaded successfully! You're authenticated! 🎉"
                    else:
                        return "❌ Config loaded but authentication failed. Check your credentials."

                except Exception as e:
                    return f"❌ Error reading config file: {str(e)}"

            def check_environment():
                """Check environment variables."""
                is_valid, issues = self.auth_manager.validate_environment()

                if is_valid:
                    auth_config = self.auth_manager.get_auth_from_env()
                    if self.auth_manager.test_authentication(auth_config):
                        return "✅ Environment configured correctly! Modal is ready!"
                    else:
                        return "⚠️ Environment variables found but authentication failed."
                else:
                    if issues:
                        return "❌ Issues found:\n" + "\n".join(f"  - {issue}" for issue in issues)
                    else:
                        return "❌ Modal environment variables not found."

            # Connect events
            open_modal_btn.click(fn=open_modal_tokens_page, outputs=auth_result)

            authenticate_btn.click(
                fn=authenticate_with_tokens,
                inputs=[token_id_input, token_secret_input, workspace_input],
                outputs=[auth_result, auth_status],
            )

            test_connection_btn.click(fn=test_connection, outputs=auth_result)

            config_file_upload.change(fn=handle_config_upload, inputs=config_file_upload, outputs=upload_result)

            refresh_btn.click(fn=check_environment, outputs=env_check_result)

            # Auto-check on load
            auth_interface.load(fn=lambda: (self._get_auth_status_message(), check_environment()), outputs=[auth_status, env_check_result])

        return auth_interface

    def _get_auth_status_message(self) -> str:
        """Get current authentication status message."""
        if self.auth_state["is_authenticated"]:
            workspace = self.auth_state.get("workspace", "default")
            return f"✅ Authenticated to Modal (Workspace: {workspace})"

        # Check environment
        auth_config = self.auth_manager.get_auth_from_env()
        if auth_config and self.auth_manager.test_authentication(auth_config):
            self.auth_state["is_authenticated"] = True
            self.auth_state["auth_config"] = auth_config
            return f"✅ Authenticated via environment variables"

        return "❌ Not authenticated - Please complete setup above"

    def create_mini_auth_status(self) -> gr.Group:
        """Create a mini auth status widget for embedding in other interfaces."""
        with gr.Group() as mini_auth:
            with gr.Row():
                auth_indicator = gr.HTML(value=self._get_mini_status_html(), elem_id="auth-indicator")
                auth_btn = gr.Button("🔐 Setup Modal Auth", size="sm", visible=not self.auth_state["is_authenticated"])

        return mini_auth, auth_indicator, auth_btn

    def _get_mini_status_html(self) -> str:
        """Get HTML for mini status indicator."""
        if self.auth_state["is_authenticated"]:
            return """
            <div style="display: flex; align-items: center; gap: 8px; color: #10b981;">
                <span style="font-size: 20px;">✅</span>
                <span>Modal Connected</span>
            </div>
            """
        else:
            return """
            <div style="display: flex; align-items: center; gap: 8px; color: #ef4444;">
                <span style="font-size: 20px;">❌</span>
                <span>Modal Not Connected</span>
            </div>
            """

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        if self.auth_state["is_authenticated"]:
            return True

        # Check environment
        auth_config = self.auth_manager.get_auth_from_env()
        if auth_config and self.auth_manager.test_authentication(auth_config):
            self.auth_state["is_authenticated"] = True
            return True

        return False


# Global authenticator instance
dashboard_auth = DashboardAuthenticator()
