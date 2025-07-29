"""Enhanced authentication and key management utilities."""

import asyncio
import os
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import find_dotenv, load_dotenv, set_key
from loguru import logger
from modal.token_flow import _new_token
from rich.console import Console
from rich.prompt import Prompt

console = Console()


class ModalAuthManager:
    """Enhanced Modal authentication manager."""

    def __init__(self):
        """Initialize the auth manager."""
        self.env_file = find_dotenv() or ".env"
        load_dotenv(self.env_file)

    def check_auth_status(self) -> dict[str, Any]:
        """Check Modal authentication status.

        Returns:
            dict: Authentication status information
        """
        try:
            # Check environment variables
            token_id = os.getenv("MODAL_TOKEN_ID")
            token_secret = os.getenv("MODAL_TOKEN_SECRET")

            if token_id and token_secret:
                return {
                    "authenticated": True,
                    "method": "environment_variables",
                    "token_id": token_id[:8] + "..." if len(token_id) > 8 else token_id,
                    "config_file": self.env_file,
                }

            # Check for modal config file
            modal_config = Path.home() / ".modal.toml"
            if modal_config.exists():
                return {"authenticated": True, "method": "modal_config", "config_file": str(modal_config)}

            return {"authenticated": False, "method": None, "error": "No Modal authentication found"}
        except Exception as e:
            logger.error(f"Error checking Modal authentication: {e}")
            return {"authenticated": False, "method": None, "error": str(e)}

    def setup_env_auth(self, token_id: str | None = None, token_secret: str | None = None) -> bool:
        """Setup Modal authentication via environment variables.

        Args:
            token_id: Modal token ID (will prompt if not provided)
            token_secret: Modal token secret (will prompt if not provided)

        Returns:
            bool: True if setup was successful
        """
        try:
            if not token_id:
                console.print("🔐 Setting up Modal authentication via environment variables")
                console.print("Get your tokens from: https://modal.com/tokens")
                token_id = Prompt.ask("Modal Token ID", password=False)

            if not token_secret:
                token_secret = Prompt.ask("Modal Token Secret", password=True)

            if token_id and token_secret:
                # Save to .env file
                set_key(self.env_file, "MODAL_TOKEN_ID", token_id)
                set_key(self.env_file, "MODAL_TOKEN_SECRET", token_secret)

                # Also set in current environment
                os.environ["MODAL_TOKEN_ID"] = token_id
                os.environ["MODAL_TOKEN_SECRET"] = token_secret

                console.print(f"✅ Modal tokens saved to {self.env_file}")
                return True
            else:
                console.print("❌ Both token ID and secret are required")
                return False

        except Exception as e:
            logger.error(f"Failed to setup environment auth: {e}")
            console.print(f"❌ Setup failed: {e}")
            return False

    def create_env_template(self) -> bool:
        """Create a .env.example template file.

        Returns:
            bool: True if template was created successfully
        """
        try:
            env_example_content = """# Modal for Noobs Configuration

# Modal Authentication (get from https://modal.com/tokens)
MODAL_TOKEN_ID=your_modal_token_id_here
MODAL_TOKEN_SECRET=your_modal_token_secret_here

# Application Settings
LOG_LEVEL=INFO
DEBUG=false
ENVIRONMENT=development

# Optional: Custom deployment settings
DEFAULT_DEPLOYMENT_MODE=minimum
DEFAULT_TIMEOUT_MINUTES=60
"""

            env_example_path = Path(".env.example")
            if not env_example_path.exists():
                env_example_path.write_text(env_example_content)
                console.print(f"✅ Created .env.example template")
                return True
            else:
                console.print("ℹ️ .env.example already exists")
                return True

        except Exception as e:
            logger.error(f"Failed to create .env template: {e}")
            console.print(f"❌ Template creation failed: {e}")
            return False

    async def setup_token_flow_auth(self, next_url: str | None = None) -> bool:
        """Run Modal's public token flow to obtain credentials.

        Args:
            next_url: Optional URL to redirect the browser after auth.

        Returns:
            bool: True if authentication succeeded.
        """
        try:
            await _new_token(activate=True, next_url=next_url)
            console.print("✅ Modal authentication completed via public link")
            return True
        except Exception as e:
            logger.error(f"Token flow authentication failed: {e}")
            console.print(f"❌ Authentication failed: {e}")
            return False

    def open_signup_page(self) -> bool:
        """Open Modal's sign-up page in a web browser."""
        url = "https://modal.com/signup"
        try:
            webbrowser.open(url, new=2)
            console.print(f"🌐 Opening sign-up page: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to open sign-up page: {e}")
            console.print(f"Visit {url} to create an account. Error: {e}")
            return False

    def validate_tokens(self) -> dict[str, Any]:
        """Validate current Modal tokens.

        Returns:
            dict: Validation result
        """
        try:
            auth_status = self.check_auth_status()

            if not auth_status["authenticated"]:
                return {
                    "valid": False,
                    "error": "No authentication configured",
                    "recommendation": "Run 'modal-for-noobs auth' to configure authentication",
                }

            # Basic format validation
            token_id = os.getenv("MODAL_TOKEN_ID")
            token_secret = os.getenv("MODAL_TOKEN_SECRET")

            if token_id and token_secret:
                # Basic validation - Modal tokens have specific formats
                if not token_id.startswith(("ak-", "st-")):
                    return {
                        "valid": False,
                        "error": "Invalid token ID format",
                        "recommendation": "Check your token ID from Modal dashboard",
                    }

                if len(token_secret) < 32:
                    return {
                        "valid": False,
                        "error": "Token secret appears too short",
                        "recommendation": "Check your token secret from Modal dashboard",
                    }

                return {
                    "valid": True,
                    "method": auth_status["method"],
                    "token_id_preview": token_id[:8] + "..." if len(token_id) > 8 else token_id,
                }

            # If using modal config file, assume it's valid for now
            return {"valid": True, "method": auth_status["method"]}

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return {"valid": False, "error": str(e), "recommendation": "Check your authentication configuration"}

    def get_auth_info(self) -> dict[str, Any]:
        """Get comprehensive authentication information.

        Returns:
            dict: Complete auth status and recommendations
        """
        try:
            status = self.check_auth_status()
            validation = self.validate_tokens()

            return {
                "status": status,
                "validation": validation,
                "env_file": self.env_file,
                "env_exists": Path(self.env_file).exists(),
                "modal_config_exists": (Path.home() / ".modal.toml").exists(),
            }
        except Exception as e:
            logger.error(f"Failed to get auth info: {e}")
            return {"error": str(e), "status": {"authenticated": False}, "validation": {"valid": False}}
