"""Common utilities and constants for CLI helpers."""

from rich import print as rprint

# Modal's official color palette
MODAL_GREEN = "#7FEE64"  # Primary brand green (RGB: 127, 238, 100)
MODAL_LIGHT_GREEN = "#DDFFDC"  # Light green tint (RGB: 221, 255, 220)
MODAL_DARK_GREEN = "#323835"  # Dark green accent (RGB: 50, 56, 53)
MODAL_BLACK = "#000000"  # Pure black background


def print_success(message: str):
    """Print success message with Modal green styling."""
    rprint(f"[{MODAL_GREEN}]✅ {message}[/{MODAL_GREEN}]")


def print_error(message: str):
    """Print error message."""
    rprint(f"[red]❌ {message}[/red]")


def print_warning(message: str):
    """Print warning message."""
    rprint(f"[yellow]⚠️  {message}[/yellow]")


def print_info(message: str):
    """Print info message with Modal styling."""
    rprint(f"[{MODAL_LIGHT_GREEN}]ℹ️  {message}[/{MODAL_LIGHT_GREEN}]")  # noqa: RUF001


def print_modal_banner(br_huehuehue: bool = False):
    """Print Modal-themed banner following their minimalist dark-mode design philosophy."""
    import secrets

    from rich.align import Align
    from rich.panel import Panel
    from rich.text import Text

    from modal_for_noobs.config_loader import config_loader

    # Load marketing content
    marketing = config_loader.load_modal_marketing()

    # Create banner text with Modal's official color palette and typography hierarchy
    banner_text = Text()
    banner_text.append("🚀 ", style="bold white")
    banner_text.append("MODAL", style=f"bold {MODAL_GREEN}")  # Primary brand green
    banner_text.append("-FOR-", style=f"bold white on {MODAL_BLACK}")  # High contrast on black
    banner_text.append("NOOBS", style=f"bold {MODAL_LIGHT_GREEN}")  # Light green accent
    banner_text.append(" 🚀", style="bold white")

    # Add ego boost content with design hierarchy
    if br_huehuehue and "portuguese" in marketing:
        hero_content = marketing["portuguese"].get("hero", "")
        features = marketing["portuguese"].get("features", [])
    else:
        hero_content = marketing.get("banners", {}).get("hero", "")
        features = marketing.get("features", [])

    if hero_content:
        banner_text.append(f"\n\n{hero_content}", style=f"bold {MODAL_LIGHT_GREEN}")

    # Add feature highlight with subtle styling
    if features:
        feature = secrets.choice(features)
        banner_text.append(f"\n{feature}", style=f"dim {MODAL_LIGHT_GREEN}")

    # Add technical tagline reflecting Modal's high-performance focus
    banner_text.append("\nHigh-Performance Cloud Computing • Zero-Config Deployment", style=f"dim {MODAL_DARK_GREEN}")

    # Panel with Modal's signature green and minimalist design
    rprint(
        Panel(
            Align.center(banner_text),
            style=f"{MODAL_GREEN}",
            border_style=f"{MODAL_GREEN}",
            padding=(1, 2),
            title="[bold white]modal-for-noobs[/bold white]",
            title_align="center",
            subtitle=f"[dim {MODAL_LIGHT_GREEN}]Powered by Modal Labs[/dim {MODAL_LIGHT_GREEN}]",
            subtitle_align="center",
        )
    )
