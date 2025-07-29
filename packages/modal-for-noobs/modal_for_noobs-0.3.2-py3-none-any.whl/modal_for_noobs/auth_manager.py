"""Enhanced Modal Authentication Manager with better token handling."""

import json
import os
import subprocess
import webbrowser
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger
from rich import print as rprint

from modal_for_noobs.cli_helpers.common import MODAL_GREEN, MODAL_LIGHT_GREEN


@dataclass
class ModalAuthConfig:
    """Modal authentication configuration."""

    token_id: str
    token_secret: str
    workspace: str | None = None

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the authentication configuration.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not self.token_id:
            errors.append("Token ID cannot be empty")
        elif not self.token_id.startswith("ak-"):
            errors.append("Token ID must start with 'ak-'")

        if not self.token_secret:
            errors.append("Token secret cannot be empty")
        elif not self.token_secret.startswith("as-"):
            errors.append("Token secret must start with 'as-'")

        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "ModalAuthConfig":
        """Create from dictionary."""
        return cls(**data)


class ModalAuthManager:
    """Manages Modal authentication with enhanced token handling."""

    def __init__(self):
        """Initialize the auth manager."""
        self.config_dir = Path.home() / ".modal-for-noobs"
        self.auth_file = self.config_dir / "auth.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(exist_ok=True, parents=True)

    def get_auth_from_env(self) -> ModalAuthConfig | None:
        """Get authentication config from environment variables.

        Returns:
            ModalAuthConfig if found, None otherwise
        """
        token_id = os.environ.get("MODAL_TOKEN_ID")
        token_secret = os.environ.get("MODAL_TOKEN_SECRET")
        workspace = os.environ.get("MODAL_WORKSPACE")

        if token_id and token_secret:
            return ModalAuthConfig(token_id=token_id, token_secret=token_secret, workspace=workspace)

        return None

    def apply_auth_to_env(self, config: ModalAuthConfig) -> None:
        """Apply authentication config to environment variables.

        Args:
            config: The authentication configuration to apply
        """
        os.environ["MODAL_TOKEN_ID"] = config.token_id
        os.environ["MODAL_TOKEN_SECRET"] = config.token_secret

        if config.workspace:
            os.environ["MODAL_WORKSPACE"] = config.workspace

    def validate_environment(self) -> tuple[bool, list[str]]:
        """Validate Modal environment variables.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        token_id = os.environ.get("MODAL_TOKEN_ID")
        token_secret = os.environ.get("MODAL_TOKEN_SECRET")

        if not token_id:
            issues.append("MODAL_TOKEN_ID not found in environment variables")
        elif not token_id.startswith("ak-"):
            issues.append("MODAL_TOKEN_ID must start with 'ak-'")

        if not token_secret:
            issues.append("MODAL_TOKEN_SECRET not found in environment variables")
        elif not token_secret.startswith("as-"):
            issues.append("MODAL_TOKEN_SECRET must start with 'as-'")

        return len(issues) == 0, issues

    def test_authentication(self, config: ModalAuthConfig) -> bool:
        """Test authentication with Modal.

        Args:
            config: The authentication configuration to test

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Set environment temporarily for test
            original_token_id = os.environ.get("MODAL_TOKEN_ID")
            original_token_secret = os.environ.get("MODAL_TOKEN_SECRET")
            original_workspace = os.environ.get("MODAL_WORKSPACE")

            # Apply test config
            self.apply_auth_to_env(config)

            # Test with modal CLI
            result = subprocess.run(["modal", "profile", "current"], capture_output=True, text=True, timeout=30)

            # Restore original environment
            if original_token_id:
                os.environ["MODAL_TOKEN_ID"] = original_token_id
            elif "MODAL_TOKEN_ID" in os.environ:
                del os.environ["MODAL_TOKEN_ID"]

            if original_token_secret:
                os.environ["MODAL_TOKEN_SECRET"] = original_token_secret
            elif "MODAL_TOKEN_SECRET" in os.environ:
                del os.environ["MODAL_TOKEN_SECRET"]

            if original_workspace:
                os.environ["MODAL_WORKSPACE"] = original_workspace
            elif "MODAL_WORKSPACE" in os.environ:
                del os.environ["MODAL_WORKSPACE"]

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Authentication test failed: {e}")
            return False

    def save_auth(self, config: ModalAuthConfig) -> bool:
        """Save authentication config to file.

        Args:
            config: The authentication configuration to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(exist_ok=True)

            # Save to JSON file
            with open(self.auth_file, "w") as f:
                json.dump(config.to_dict(), f, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to save auth config: {e}")
            return False

    def load_auth(self) -> ModalAuthConfig | None:
        """Load authentication config from file.

        Returns:
            ModalAuthConfig if found, None otherwise
        """
        try:
            if self.auth_file.exists():
                with open(self.auth_file) as f:
                    data = json.load(f)
                return ModalAuthConfig.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load auth config: {e}")

        return None

    def setup_env_auth(self, token_id: str, token_secret: str, workspace: str = None) -> bool:
        """Set up environment-based authentication.

        Args:
            token_id: Modal token ID
            token_secret: Modal token secret
            workspace: Optional workspace name

        Returns:
            True if successful, False otherwise
        """
        try:
            config = ModalAuthConfig(token_id=token_id, token_secret=token_secret, workspace=workspace)

            # Validate config
            is_valid, errors = config.validate()
            if not is_valid:
                logger.error(f"Invalid config: {errors}")
                return False

            # Test authentication
            if not self.test_authentication(config):
                logger.error("Authentication test failed")
                return False

            # Apply to environment and save
            self.apply_auth_to_env(config)
            self.save_auth(config)

            return True

        except Exception as e:
            logger.error(f"Failed to setup auth: {e}")
            return False

    def open_signup_page(self) -> None:
        """Open Modal signup page in browser."""
        try:
            webbrowser.open("https://modal.com/signup")
        except Exception as e:
            logger.error(f"Failed to open signup page: {e}")

    def open_tokens_page(self) -> None:
        """Open Modal tokens page in browser."""
        try:
            webbrowser.open("https://modal.com/settings/tokens")
        except Exception as e:
            logger.error(f"Failed to open tokens page: {e}")

    def get_auth_status(self) -> dict[str, any]:
        """Get current authentication status.

        Returns:
            Dictionary with authentication status information
        """
        # Check environment first
        config = self.get_auth_from_env()
        if config and self.test_authentication(config):
            return {
                "authenticated": True,
                "source": "environment",
                "workspace": config.workspace,
                "token_id": config.token_id[:10] + "..." if config.token_id else None,
            }

        # Check saved config
        config = self.load_auth()
        if config and self.test_authentication(config):
            return {
                "authenticated": True,
                "source": "saved_config",
                "workspace": config.workspace,
                "token_id": config.token_id[:10] + "..." if config.token_id else None,
            }

        return {"authenticated": False, "source": None, "workspace": None, "token_id": None}


# Global auth manager instance
auth_manager = ModalAuthManager()
