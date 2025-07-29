"""Modal-for-noobs: Easy Modal deployment for Gradio apps."""

__version__ = "0.2.5"
__author__ = "Arthur Souza Rodrigues"
__email__ = "arthrod@umich.edu"

from modal_for_noobs.cli import app, main
from modal_for_noobs.config import config
from modal_for_noobs.modal_deploy import ModalDeployer

__all__ = ["__author__", "__email__", "__version__", "ModalDeployer", "app", "config", "main"]
