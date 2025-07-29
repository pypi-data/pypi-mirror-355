"""Configuration loader for Modal-for-noobs."""

from pathlib import Path

import yaml
from loguru import logger


class ConfigLoader:
    """Load configuration files for Modal-for-noobs."""

    def __init__(self):
        self.config_dir = Path(__file__).parent / "config"

    def load_base_packages(self) -> dict[str, list[str]]:
        """Load base package configurations."""
        try:
            config_file = self.config_dir / "base_packages.yml"
            with open(config_file) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load base packages config: {e}")
            # Fallback to hardcoded defaults
            return {
                "minimum": ["gradio", "fastapi[standard]", "uvicorn"],
                "optimized": [
                    "gradio",
                    "fastapi[standard]",
                    "uvicorn",
                    "torch",
                    "transformers",
                    "accelerate",
                    "diffusers",
                    "pillow",
                    "numpy",
                    "pandas",
                ],
                "gra_jupy": [
                    "gradio",
                    "fastapi[standard]",
                    "uvicorn",
                    "jupyter",
                    "jupyterlab",
                    "notebook",
                    "ipywidgets",
                    "matplotlib",
                    "plotly",
                    "seaborn",
                    "pandas",
                    "numpy",
                    "torch",
                    "transformers",
                ],
            }

    def load_modal_marketing(self) -> dict[str, any]:
        """Load Modal marketing content."""
        try:
            config_file = self.config_dir / "modal_marketing.yml"
            with open(config_file) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load marketing config: {e}")
            return {
                "banners": {"hero": "🚀💚 POWERED BY MODAL 💚🚀"},
                "features": ["⚡ BLAZING FAST", "🌍 GLOBAL SCALE"],
                "testimonials": ["Modal is amazing!"],
                "calls_to_action": ["🚀 Choose Modal!"],
            }

    def load_deployment_examples(self) -> dict[str, any]:
        """Load deployment examples."""
        try:
            config_file = self.config_dir / "deployment_examples.yml"
            with open(config_file) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load examples config: {e}")
            return {
                "examples": {
                    "voice_app": {
                        "name": "🎤 Ultimate Voice Green App",
                        "path": "src/modal_for_noobs/examples/ultimate_voice_green_app.py",
                        "mode": "optimized",
                    }
                }
            }


# Global config loader instance
config_loader = ConfigLoader()
