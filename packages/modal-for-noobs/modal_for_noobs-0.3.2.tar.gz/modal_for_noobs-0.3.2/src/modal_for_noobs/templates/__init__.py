"""Template system for Modal deployment generation.

This module provides Python-based template functions for generating
Modal deployment files from Gradio applications.
"""

from modal_for_noobs.templates.deployment import (
    generate_modal_deployment,
    generate_modal_deployment_legacy,
    get_image_config,
)

__all__ = [
    "generate_modal_deployment",
    "generate_modal_deployment_legacy",
    "get_image_config",
]
