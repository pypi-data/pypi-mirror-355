"""Configuration management helpers for modal-for-noobs CLI."""

import json
from pathlib import Path
from typing import Any, Dict

import typer
from rich import print as rprint
from rich.align import Align
from rich.panel import Panel
from rich.text import Text

from modal_for_noobs.cli_helpers.common import MODAL_GREEN, MODAL_LIGHT_GREEN, print_error, print_info, print_success, print_warning
from modal_for_noobs.config_loader import config_loader


def show_config_info(br_huehuehue: bool = False):
    """Show current configuration information."""
    # Load configurations
    packages = config_loader.load_base_packages()
    examples = config_loader.load_deployment_examples()

    if br_huehuehue:
        config_text = Text()
        config_text.append("⚙️ INFORMAÇÕES DE CONFIGURAÇÃO ⚙️", style=f"bold {MODAL_GREEN}")
        config_text.append("\n🇧🇷 Configurações atuais do modal-for-noobs! Huehuehue! 🇧🇷", style="bold white")
    else:
        config_text = Text()
        config_text.append("⚙️ CONFIGURATION INFORMATION ⚙️", style=f"bold {MODAL_GREEN}")
        config_text.append("\n📋 Current modal-for-noobs settings and available options", style="bold white")

    rprint(Panel(Align.center(config_text), border_style=f"{MODAL_GREEN}", padding=(1, 2)))

    # Show deployment modes
    if br_huehuehue:
        rprint(f"\n[bold {MODAL_GREEN}]🚀 Modos de Deployment:[/bold {MODAL_GREEN}]")
    else:
        rprint(f"\n[bold {MODAL_GREEN}]🚀 Deployment Modes:[/bold {MODAL_GREEN}]")

    for mode, pkgs in packages.items():
        mode_display = {
            "minimum": "🌱 Minimum (CPU)",
            "optimized": "⚡ Optimized (GPU + vLLM)",
            "gra_jupy": "🪐 Gradio + Jupyter",
            "marimo": "📓 Marimo (Reactive notebooks)",
        }.get(mode, f"🔧 {mode.title()}")

        pkg_count = len(pkgs)
        sample_pkgs = ", ".join(pkgs[:3])
        if pkg_count > 3:
            sample_pkgs += f"... (+{pkg_count - 3} more)"

        rprint(f"  {mode_display}")
        rprint(f"    Packages: {sample_pkgs}")

    # Show current user config
    if br_huehuehue:
        rprint(f"\n[bold {MODAL_GREEN}]🛠️ Configurações do Usuário:[/bold {MODAL_GREEN}]")
    else:
        rprint(f"\n[bold {MODAL_GREEN}]🛠️ User Configuration:[/bold {MODAL_GREEN}]")

    user_config = get_user_config()
    if user_config:
        for key, value in user_config.items():
            rprint(f"  • {key}: [bold]{value}[/bold]")
    else:
        if br_huehuehue:
            rprint("  Nenhuma configuração personalizada definida")
        else:
            rprint("  No custom configuration set")

    # Show examples
    if br_huehuehue:
        rprint(f"\n[bold {MODAL_GREEN}]🎯 Exemplos Disponíveis:[/bold {MODAL_GREEN}]")
    else:
        rprint(f"\n[bold {MODAL_GREEN}]🎯 Available Examples:[/bold {MODAL_GREEN}]")

    if examples and "examples" in examples:
        for name, example in list(examples["examples"].items())[:5]:
            rprint(f"  • {example.get('name', name)}")

    if br_huehuehue:
        rprint(f"\n[{MODAL_LIGHT_GREEN}]💡 Use 'config --wizard' para configurar interativamente![/{MODAL_LIGHT_GREEN}]")
    else:
        rprint(f"\n[{MODAL_LIGHT_GREEN}]💡 Use 'config --wizard' for interactive configuration![/{MODAL_LIGHT_GREEN}]")


def run_config_wizard(br_huehuehue: bool = False):
    """Run interactive configuration wizard."""
    from modal_for_noobs.cli_helpers.auth_helper import install_mn_alias

    if br_huehuehue:
        wizard_text = Text()
        wizard_text.append("🧙‍♂️ ASSISTENTE DE CONFIGURAÇÃO 🧙‍♂️", style=f"bold {MODAL_GREEN}")
        wizard_text.append("\n🇧🇷 Vamos configurar tudo juntinhos! Huehuehue! 🇧🇷", style="bold white")
    else:
        wizard_text = Text()
        wizard_text.append("🧙‍♂️ CONFIGURATION WIZARD 🧙‍♂️", style=f"bold {MODAL_GREEN}")
        wizard_text.append("\n⚡ Let's set up your modal-for-noobs preferences!", style="bold white")

    rprint(Panel(Align.center(wizard_text), border_style=f"{MODAL_GREEN}", padding=(1, 2)))

    user_config = get_user_config()

    # Step 1: Default deployment mode
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]🚀 Passo 1: Modo de Deployment Padrão[/{MODAL_GREEN}]")
        rprint("Qual modo você quer usar por padrão?")
    else:
        rprint(f"\n[{MODAL_GREEN}]🚀 Step 1: Default Deployment Mode[/{MODAL_GREEN}]")
        rprint("Which deployment mode do you want to use by default?")

    modes = {
        "1": ("minimum", "🌱 Minimum - Fast, CPU-only, basic packages"),
        "2": ("optimized", "⚡ Optimized - GPU support, vLLM, ML libraries"),
        "3": ("gra_jupy", "🪐 Gradio + Jupyter - Interactive notebooks"),
        "4": ("marimo", "📓 Marimo - Reactive Python notebooks"),
    }

    for key, (mode, desc) in modes.items():
        rprint(f"  [{key}] {desc}")

    current_default = user_config.get("default_mode", "minimum")
    current_num = next((k for k, (m, _) in modes.items() if m == current_default), "1")

    if br_huehuehue:
        choice = typer.prompt(f"Escolha [1-4] (atual: {current_num})", default=current_num)
    else:
        choice = typer.prompt(f"Choose [1-4] (current: {current_num})", default=current_num)

    if choice in modes:
        user_config["default_mode"] = modes[choice][0]
        print_success(f"Default mode set to: {modes[choice][1]}")

    # Step 2: Default timeout
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]⏱️ Passo 2: Timeout Padrão (minutos)[/{MODAL_GREEN}]")
        current_timeout = user_config.get("default_timeout", 60)
        timeout = typer.prompt(f"Timeout em minutos (atual: {current_timeout})", default=current_timeout, type=int)
    else:
        rprint(f"\n[{MODAL_GREEN}]⏱️ Step 2: Default Timeout (minutes)[/{MODAL_GREEN}]")
        current_timeout = user_config.get("default_timeout", 60)
        timeout = typer.prompt(f"Timeout in minutes (current: {current_timeout})", default=current_timeout, type=int)

    user_config["default_timeout"] = timeout
    print_success(f"Default timeout set to: {timeout} minutes")

    # Step 3: Auto-install mn alias
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]🔗 Passo 3: Comando Global 'mn'[/{MODAL_GREEN}]")
        install_mn = typer.confirm("Instalar o comando global 'mn' agora?", default=True)
    else:
        rprint(f"\n[{MODAL_GREEN}]🔗 Step 3: Global 'mn' Command[/{MODAL_GREEN}]")
        install_mn = typer.confirm("Install global 'mn' command now?", default=True)

    if install_mn:
        success = install_mn_alias(None, True, br_huehuehue)
        if success:
            print_success("Global 'mn' command installed!")
        else:
            print_warning("Failed to install global 'mn' command")

    # Save configuration
    save_user_config(user_config)

    if br_huehuehue:
        print_success("Configuração salva com sucesso! Huehuehue!")
        print_info("Use 'config --info' para ver suas configurações")
    else:
        print_success("Configuration saved successfully!")
        print_info("Use 'config --info' to view your settings")


def set_config_value(set_value: str, br_huehuehue: bool = False):
    """Set a configuration value."""
    if "=" not in set_value:
        if br_huehuehue:
            print_error("Formato inválido! Use: chave=valor")
        else:
            print_error("Invalid format! Use: key=value")
        return

    key, value = set_value.split("=", 1)
    key = key.strip()
    value = value.strip()

    # Validate key
    valid_keys = ["default_mode", "default_timeout", "auto_install_deps", "preferred_gpu"]
    if key not in valid_keys:
        if br_huehuehue:
            print_error(f"Chave inválida: {key}")
            print_info(f"Chaves válidas: {', '.join(valid_keys)}")
        else:
            print_error(f"Invalid key: {key}")
            print_info(f"Valid keys: {', '.join(valid_keys)}")
        return

    # Type conversion
    if key == "default_timeout":
        try:
            value = int(value)
        except ValueError:
            print_error("Timeout must be an integer (minutes)")
            return
    elif key == "auto_install_deps":
        value = value.lower() in ("true", "1", "yes", "on")

    user_config = get_user_config()
    user_config[key] = value
    save_user_config(user_config)

    if br_huehuehue:
        print_success(f"Configuração salva: {key} = {value}")
    else:
        print_success(f"Configuration set: {key} = {value}")


def get_config_value(get_value: str, br_huehuehue: bool = False):
    """Get a configuration value."""
    user_config = get_user_config()

    if get_value in user_config:
        rprint(f"[bold]{get_value}[/bold]: {user_config[get_value]}")
    else:
        if br_huehuehue:
            print_warning(f"Configuração '{get_value}' não encontrada")
        else:
            print_warning(f"Configuration '{get_value}' not found")


def list_config_keys(br_huehuehue: bool = False):
    """List all configuration keys."""
    if br_huehuehue:
        rprint(f"[bold {MODAL_GREEN}]🔧 Chaves de Configuração Disponíveis:[/bold {MODAL_GREEN}]")
    else:
        rprint(f"[bold {MODAL_GREEN}]🔧 Available Configuration Keys:[/bold {MODAL_GREEN}]")

    config_keys = {
        "default_mode": "Default deployment mode (minimum, optimized, gra_jupy, marimo)",
        "default_timeout": "Default timeout in minutes (integer)",
        "auto_install_deps": "Auto-install dependencies (true/false)",
        "preferred_gpu": "Preferred GPU type (any, a100, t4, etc.)",
    }

    user_config = get_user_config()

    for key, description in config_keys.items():
        current_value = user_config.get(key, "not set")
        rprint(f"  • [bold]{key}[/bold]: {description}")
        rprint(f"    Current value: [dim]{current_value}[/dim]")


def get_user_config() -> dict[str, Any]:
    """Get user configuration from file."""
    config_file = Path.home() / ".modal-for-noobs" / "config.json"

    if config_file.exists():
        try:
            return json.loads(config_file.read_text())
        except Exception:
            return {}
    return {}


def save_user_config(config_data: dict[str, Any]):
    """Save user configuration to file."""
    config_dir = Path.home() / ".modal-for-noobs"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"

    config_file.write_text(json.dumps(config_data, indent=2))
