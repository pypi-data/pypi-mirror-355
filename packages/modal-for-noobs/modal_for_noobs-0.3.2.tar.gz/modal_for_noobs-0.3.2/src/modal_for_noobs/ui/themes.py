"""Beautiful Modal-themed Gradio themes and styling.

This module provides Modal-branded themes and CSS styling for Gradio interfaces,
using the official Modal color palette from cli_helpers.common.
"""

import gradio as gr

# Import Modal's official color palette
from modal_for_noobs.cli_helpers.common import MODAL_BLACK, MODAL_DARK_GREEN, MODAL_GREEN, MODAL_LIGHT_GREEN


def create_modal_theme() -> gr.Theme:
    """Create a beautiful Modal-themed Gradio theme using official Modal colors.

    Returns:
        gr.Theme: Modal-themed Gradio theme with signature green colors
    """
    # Use Modal's official color palette
    modal_green = MODAL_GREEN  # "#7FEE64"
    modal_light_green = MODAL_LIGHT_GREEN  # "#DDFFDC"
    modal_dark_green = MODAL_DARK_GREEN  # "#323835"
    modal_black = MODAL_BLACK  # "#000000"

    try:
        theme = gr.themes.Soft()
    except Exception:
        # Fallback to default theme if soft theme not available
        theme = gr.themes.Default()

    # Customize with Modal colors - only use supported parameters
    try:
        theme = theme.set(
            # Primary button styling
            button_primary_background_fill=modal_green,
            button_primary_background_fill_hover=modal_light_green,
            button_primary_text_color=modal_black,
            # Secondary button styling
            button_secondary_background_fill=f"rgba(127, 238, 100, 0.1)",  # MODAL_GREEN with alpha
            button_secondary_background_fill_hover=f"rgba(127, 238, 100, 0.2)",
            button_secondary_text_color=modal_dark_green,
            button_secondary_border_color=modal_green,
            # Input and form styling
            input_background_fill="white",
            input_border_color=modal_green,
            # General panel styling
            panel_background_fill="white",
            panel_border_color=f"rgba(127, 238, 100, 0.2)",  # MODAL_GREEN with alpha
            # Body background with subtle Modal green gradient
            body_background_fill=f"rgba(127, 238, 100, 0.02)",
            # Text colors
            body_text_color="#1f2937",
            # Link colors
            link_text_color=modal_green,
            link_text_color_hover=modal_light_green,
            # Block styling
            block_background_fill="white",
            block_border_color=f"rgba(127, 238, 100, 0.15)",  # MODAL_GREEN with alpha
            # Font family - removed font parameter due to compatibility issues
            # font=("SF Pro Display", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"),
        )
    except Exception as e:
        # If theme customization fails, just return the base theme
        print(f"Warning: Could not fully customize theme: {e}")

    return theme


def get_modal_css() -> str:
    """Get additional CSS for enhanced Modal styling using official Modal colors.

    Returns:
        str: CSS string with Modal-specific enhancements
    """
    modal_green = MODAL_GREEN  # "#7FEE64"
    modal_light_green = MODAL_LIGHT_GREEN  # "#DDFFDC"
    modal_dark_green = MODAL_DARK_GREEN  # "#323835"
    modal_black = MODAL_BLACK  # "#000000"

    return f"""
    /* MODAL ENHANCED STYLING */

    /* Font family styling for better compatibility */
    body, .gr-app {{
        font-family: "SF Pro Display", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", sans-serif !important;
    }}

    /* Custom button hover effects */
    .gr-button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(127, 238, 100, 0.3) !important;
    }}

    /* Enhanced input focus */
    .gr-textbox:focus-within,
    .gr-dropdown:focus-within {{
        box-shadow: 0 0 0 3px rgba(127, 238, 100, 0.2) !important;
        border-color: {modal_green} !important;
    }}

    /* Beautiful tab styling */
    .gr-tab-nav button {{
        border-radius: 8px 8px 0 0 !important;
        border-bottom: none !important;
        font-weight: 600 !important;
    }}

    .gr-tab-nav button.selected {{
        background: {modal_green} !important;
        color: {modal_black} !important;
        border-color: {modal_green} !important;
    }}

    .gr-tab-nav button:not(.selected) {{
        background: rgba(127, 238, 100, 0.05) !important;
        color: {modal_dark_green} !important;
        border-color: rgba(127, 238, 100, 0.2) !important;
    }}

    .gr-tab-nav button:not(.selected):hover {{
        background: rgba(127, 238, 100, 0.1) !important;
        color: {modal_green} !important;
    }}

    /* Markdown enhancements */
    .gr-markdown h1,
    .gr-markdown h2,
    .gr-markdown h3 {{
        color: {modal_green} !important;
        font-weight: 700 !important;
    }}

    /* Modal deployment button special styling */
    .modal-deploy-button {{
        background: linear-gradient(135deg, {modal_green} 0%, {modal_light_green} 100%) !important;
        border: none !important;
        color: {modal_black} !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(127, 238, 100, 0.4) !important;
        transition: all 0.3s ease !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        cursor: pointer !important;
    }}

    .modal-deploy-button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(127, 238, 100, 0.6) !important;
        background: linear-gradient(135deg, {modal_light_green} 0%, {modal_green} 100%) !important;
    }}

    /* Primary button styling */
    .gr-button-primary {{
        background-color: {modal_green} !important;
        color: {modal_black} !important;
        border: none !important;
    }}
    
    .gr-button-secondary {{
        background-color: transparent !important;
        color: {modal_green} !important;
        border: 1px solid {modal_green} !important;
    }}
    """


# Pre-built themes for quick use
try:
    MODAL_THEME = create_modal_theme()
    MODAL_CSS = get_modal_css()
except Exception as e:
    print(f"Warning: Could not create Modal theme: {e}")
    MODAL_THEME = gr.themes.Default()
    MODAL_CSS = ""
