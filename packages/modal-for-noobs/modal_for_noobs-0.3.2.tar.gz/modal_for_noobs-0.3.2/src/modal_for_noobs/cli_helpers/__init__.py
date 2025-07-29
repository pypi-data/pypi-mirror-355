"""CLI helpers for modal-for-noobs.

This module contains helper functions and classes for organizing
the CLI functionality into manageable modules.
"""

from modal_for_noobs.cli_helpers.auth_helper import (
    install_mn_alias,
    setup_auth_async,
)
from modal_for_noobs.cli_helpers.common import (
    MODAL_BLACK,
    MODAL_DARK_GREEN,
    MODAL_GREEN,
    MODAL_LIGHT_GREEN,
    print_error,
    print_info,
    print_modal_banner,
    print_success,
    print_warning,
)
from modal_for_noobs.cli_helpers.config_helper import (
    get_config_value,
    get_user_config,
    list_config_keys,
    run_config_wizard,
    save_user_config,
    set_config_value,
    show_config_info,
)

__all__ = [
    # Config helpers
    "show_config_info",
    "run_config_wizard",
    "set_config_value",
    "get_config_value",
    "list_config_keys",
    "get_user_config",
    "save_user_config",
    # Auth helpers
    "setup_auth_async",
    "install_mn_alias",
    # Common utilities
    "MODAL_GREEN",
    "MODAL_LIGHT_GREEN",
    "MODAL_DARK_GREEN",
    "MODAL_BLACK",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "print_modal_banner",
]
