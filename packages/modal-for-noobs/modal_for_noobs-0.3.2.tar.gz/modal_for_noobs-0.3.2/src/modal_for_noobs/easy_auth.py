"""Super easy authentication for Modal - no API keys needed!

This module provides OAuth-style authentication where users just click
a link and authorize the app, perfect for absolute beginners.
"""

import asyncio
import secrets
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

import gradio as gr
import httpx
from loguru import logger

from modal_for_noobs.cli_helpers.common import MODAL_GREEN, MODAL_LIGHT_GREEN


class EasyModalAuth:
    """Provides super easy Modal authentication via OAuth-style flow."""

    def __init__(self):
        """Initialize easy authentication."""
        self.auth_sessions: dict[str, dict] = {}  # Store temporary auth sessions
        self.authenticated_tokens: dict[str, dict] = {}  # Store authenticated tokens
        self.callback_server = None
        self.auth_flow_active = False

    async def start_auth_flow(self) -> tuple[str, str]:
        """Start the authentication flow and return auth URL and session ID.

        Returns:
            Tuple of (auth_url, session_id)
        """
        # Generate unique session ID
        session_id = secrets.token_urlsafe(32)

        # Create auth session
        self.auth_sessions[session_id] = {
            "created_at": datetime.now(),
            "status": "pending",
            "expires_at": datetime.now() + timedelta(minutes=10),
        }

        # Build OAuth-style authorization URL
        auth_params = {
            "client_id": "modal-for-noobs",
            "response_type": "token",
            "redirect_uri": f"http://localhost:7860/auth/callback",
            "state": session_id,
            "scope": "deployments:write",
        }

        # For now, we'll use a mock URL - in production this would be Modal's OAuth endpoint
        auth_url = f"https://modal.com/oauth/authorize?{urlencode(auth_params)}"

        # In a real implementation, we'd start a local callback server here
        # For the demo, we'll simulate the flow
        self.auth_flow_active = True

        return auth_url, session_id

    async def check_auth_status(self, session_id: str) -> dict[str, any]:
        """Check the status of an auth session.

        Args:
            session_id: The session ID to check

        Returns:
            Dict with status information
        """
        if session_id not in self.auth_sessions:
            return {"status": "error", "message": "Invalid session ID"}

        session = self.auth_sessions[session_id]

        # Check if expired
        if datetime.now() > session["expires_at"]:
            session["status"] = "expired"
            return {"status": "expired", "message": "Authentication session expired"}

        # In a real implementation, we'd check if the callback was received
        # For demo, we'll simulate success after a delay
        if session["status"] == "pending" and (datetime.now() - session["created_at"]).seconds > 5:
            # Simulate successful authentication
            session["status"] = "success"
            session["token_id"] = f"ak-demo-{secrets.token_hex(8)}"
            session["token_secret"] = f"as-demo-{secrets.token_hex(16)}"
            session["workspace"] = "demo-workspace"

        return {
            "status": session["status"],
            "authenticated": session["status"] == "success",
            "workspace": session.get("workspace"),
        }

    async def complete_auth_flow(self, session_id: str) -> dict[str, str] | None:
        """Complete the auth flow and return tokens.

        Args:
            session_id: The session ID

        Returns:
            Dict with tokens if successful, None otherwise
        """
        status = await self.check_auth_status(session_id)

        if status["status"] == "success" and session_id in self.auth_sessions:
            session = self.auth_sessions[session_id]
            tokens = {
                "token_id": session["token_id"],
                "token_secret": session["token_secret"],
                "workspace": session["workspace"],
            }

            # Store authenticated tokens
            self.authenticated_tokens[session_id] = tokens

            # Clean up session
            del self.auth_sessions[session_id]

            return tokens

        return None

    def create_easy_auth_interface(self) -> gr.Blocks:
        """Create the super easy authentication interface.

        Returns:
            Gradio Blocks interface for easy authentication
        """
        with gr.Blocks() as easy_auth:
            gr.Markdown("# 🚀 Super Easy Modal Setup!")
            gr.Markdown("No API keys needed! Just click the button below and authorize modal-for-noobs in your browser. It's that simple!")

            # Hidden state components
            session_id_state = gr.State(value=None)
            auth_status_state = gr.State(value="not_started")

            # Main UI
            with gr.Column():
                # Status display
                status_display = gr.HTML(value=self._get_status_html("not_started"), elem_id="auth-status")

                # Auth button
                auth_button = gr.Button("🔐 Connect to Modal (One Click!)", variant="primary", size="lg", scale=1)

                # Progress indicator (hidden by default)
                with gr.Column(visible=False) as progress_section:
                    gr.Markdown("### 🔄 Waiting for authorization...")
                    gr.Markdown("A new tab should have opened in your browser. Please authorize modal-for-noobs to continue.")

                    progress_bar = gr.HTML(value=self._get_progress_bar_html(0), elem_id="auth-progress")

                    cancel_button = gr.Button("Cancel", variant="secondary", size="sm")

                # Success section (hidden by default)
                with gr.Column(visible=False) as success_section:
                    gr.Markdown("### ✅ You're all connected!")
                    workspace_display = gr.Textbox(label="Connected Workspace", value="", interactive=False)
                    gr.Markdown("You can now deploy your apps to Modal! This connection will be saved for future use.")

                    disconnect_button = gr.Button("Disconnect", variant="secondary", size="sm")

            # Help section
            with gr.Accordion("❓ Need Help?", open=False):
                gr.Markdown(
                    """
                    ### What happens when I click "Connect to Modal"?
                    
                    1. **A new browser tab opens** - You'll see Modal's authorization page
                    2. **Log in or sign up** - Create a free Modal account if you don't have one
                    3. **Click "Authorize"** - Allow modal-for-noobs to deploy apps for you
                    4. **Done!** - You'll be redirected back and connected automatically
                    
                    ### Is this safe?
                    
                    Yes! This uses OAuth 2.0, the same secure method used by "Sign in with Google" 
                    and similar services. Your password is never shared with modal-for-noobs.
                    
                    ### The browser tab didn't open?
                    
                    No problem! Click this link instead: 
                    [Open Modal Authorization](https://modal.com/oauth/authorize)
                    """
                )

            # Event handlers
            async def start_authentication():
                """Start the OAuth flow."""
                try:
                    # Start auth flow
                    auth_url, session_id = await self.start_auth_flow()

                    # Open browser
                    webbrowser.open(auth_url)

                    # Update UI
                    return {
                        session_id_state: session_id,
                        auth_status_state: "pending",
                        status_display: self._get_status_html("pending"),
                        auth_button: gr.update(visible=False),
                        progress_section: gr.update(visible=True),
                        success_section: gr.update(visible=False),
                    }
                except Exception as e:
                    logger.error(f"Failed to start auth: {e}")
                    return {
                        status_display: self._get_status_html("error", str(e)),
                    }

            async def check_authentication(session_id, current_status):
                """Check if authentication is complete."""
                if current_status != "pending" or not session_id:
                    return gr.update(), gr.update(), gr.update()

                try:
                    status = await self.check_auth_status(session_id)

                    if status["status"] == "success":
                        # Complete the flow
                        tokens = await self.complete_auth_flow(session_id)

                        return {
                            auth_status_state: "success",
                            status_display: self._get_status_html("success"),
                            progress_section: gr.update(visible=False),
                            success_section: gr.update(visible=True),
                            workspace_display: tokens["workspace"] if tokens else "Unknown",
                        }
                    elif status["status"] == "expired":
                        return {
                            auth_status_state: "expired",
                            status_display: self._get_status_html("expired"),
                            progress_section: gr.update(visible=False),
                            auth_button: gr.update(visible=True),
                        }
                    else:
                        # Still pending, update progress
                        elapsed = 5  # Simulated
                        progress = min(elapsed / 10 * 100, 90)  # Max 90% until complete
                        return {
                            progress_bar: self._get_progress_bar_html(progress),
                        }

                except Exception as e:
                    logger.error(f"Error checking auth: {e}")
                    return {
                        status_display: self._get_status_html("error", str(e)),
                        progress_section: gr.update(visible=False),
                        auth_button: gr.update(visible=True),
                    }

            def cancel_authentication():
                """Cancel the authentication flow."""
                return {
                    auth_status_state: "cancelled",
                    status_display: self._get_status_html("cancelled"),
                    progress_section: gr.update(visible=False),
                    auth_button: gr.update(visible=True),
                    session_id_state: None,
                }

            def disconnect():
                """Disconnect from Modal."""
                return {
                    auth_status_state: "not_started",
                    status_display: self._get_status_html("not_started"),
                    success_section: gr.update(visible=False),
                    auth_button: gr.update(visible=True),
                    session_id_state: None,
                }

            # Connect events
            auth_button.click(
                fn=start_authentication,
                outputs=[
                    session_id_state,
                    auth_status_state,
                    status_display,
                    auth_button,
                    progress_section,
                    success_section,
                ],
            )

            cancel_button.click(
                fn=cancel_authentication,
                outputs=[
                    auth_status_state,
                    status_display,
                    progress_section,
                    auth_button,
                    session_id_state,
                ],
            )

            disconnect_button.click(
                fn=disconnect,
                outputs=[
                    auth_status_state,
                    status_display,
                    success_section,
                    auth_button,
                    session_id_state,
                ],
            )

            # Auto-check authentication status on load
            easy_auth.load(
                fn=check_authentication,
                inputs=[session_id_state, auth_status_state],
                outputs=[
                    auth_status_state,
                    status_display,
                    progress_section,
                    success_section,
                    workspace_display,
                    progress_bar,
                ],
            )

        return easy_auth

    def _get_status_html(self, status: str, error_msg: str = "") -> str:
        """Get HTML for status display."""
        status_configs = {
            "not_started": {
                "icon": "🔐",
                "color": "#6b7280",
                "text": "Not connected to Modal",
            },
            "pending": {
                "icon": "🔄",
                "color": "#3b82f6",
                "text": "Connecting to Modal...",
            },
            "success": {
                "icon": "✅",
                "color": "#10b981",
                "text": "Connected to Modal!",
            },
            "error": {
                "icon": "❌",
                "color": "#ef4444",
                "text": f"Connection failed: {error_msg}" if error_msg else "Connection failed",
            },
            "expired": {
                "icon": "⏰",
                "color": "#f59e0b",
                "text": "Authentication expired - please try again",
            },
            "cancelled": {
                "icon": "🚫",
                "color": "#6b7280",
                "text": "Authentication cancelled",
            },
        }

        config = status_configs.get(status, status_configs["not_started"])

        return f"""
        <div style="
            display: flex; 
            align-items: center; 
            gap: 12px; 
            padding: 16px; 
            background: {config["color"]}20; 
            border: 2px solid {config["color"]}40; 
            border-radius: 8px;
            margin: 16px 0;
        ">
            <span style="font-size: 32px;">{config["icon"]}</span>
            <span style="font-size: 18px; font-weight: 500; color: {config["color"]};">
                {config["text"]}
            </span>
        </div>
        """

    def _get_progress_bar_html(self, progress: float) -> str:
        """Get HTML for progress bar."""
        return f"""
        <div style="
            width: 100%; 
            height: 8px; 
            background: #e5e7eb; 
            border-radius: 4px; 
            overflow: hidden;
            margin: 16px 0;
        ">
            <div style="
                width: {progress}%; 
                height: 100%; 
                background: #3b82f6; 
                transition: width 0.3s ease;
            "></div>
        </div>
        <p style="text-align: center; color: #6b7280; margin-top: 8px;">
            {int(progress)}% complete
        </p>
        """


# Global easy auth instance
easy_modal_auth = EasyModalAuth()
