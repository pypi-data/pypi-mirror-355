"""Enhanced CLI commands with advanced wizard functionality."""

import secrets
from pathlib import Path
from typing import Annotated, Dict, List, Optional

import questionary
import typer
from loguru import logger
from rich import print as rprint
from rich.align import Align
from rich.panel import Panel
from rich.text import Text
from slugify import slugify

from modal_for_noobs.cli_helpers.common import MODAL_GREEN, MODAL_LIGHT_GREEN
from modal_for_noobs.template_generator import (
    RemoteFunctionConfig,
    TemplateConfig,
    TemplateGenerator,
    generate_from_wizard_input,
)


def enhanced_wizard(
    app_file: Path,
    br_huehuehue: bool = False,
) -> str | None:
    """Enhanced deployment wizard with all modal_generate features.

    Args:
        app_file: Path to the Gradio app file
        br_huehuehue: Brazilian mode flag

    Returns:
        Generated deployment code or None if cancelled
    """
    # Read original code
    try:
        original_code = app_file.read_text()
    except Exception as e:
        rprint(f"[red]Error reading app file: {e}[/red]")
        return None

    # Welcome message
    wizard_text = Text()
    if br_huehuehue:
        wizard_text.append("🧙‍♂️ ASSISTENTE AVANÇADO DE DEPLOYMENT 🧙‍♂️", style=f"bold {MODAL_GREEN}")
        wizard_text.append("\n✨ Vamos criar um deployment poderoso! Huehuehue!", style="bold white")
    else:
        wizard_text.append("🧙‍♂️ ADVANCED DEPLOYMENT WIZARD 🧙‍♂️", style=f"bold {MODAL_GREEN}")
        wizard_text.append("\n✨ Let's create a powerful Modal deployment!", style="bold white")

    rprint(Panel(Align.center(wizard_text), border_style=f"{MODAL_GREEN}", padding=(1, 2)))

    # Step 1: App name and namespace
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]📱 Passo 1: Configuração Básica[/{MODAL_GREEN}]")
    else:
        rprint(f"\n[{MODAL_GREEN}]📱 Step 1: Basic Configuration[/{MODAL_GREEN}]")

    app_name = slugify(app_file.stem)
    namespace = questionary.text("Namespace prefix (optional):", default="").ask()

    if namespace:
        namespace = slugify(namespace)
        app_name = f"{namespace}-{app_name}"

    # Step 2: Deployment mode
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]⚡ Passo 2: Modo de Deployment[/{MODAL_GREEN}]")
    else:
        rprint(f"\n[{MODAL_GREEN}]⚡ Step 2: Deployment Mode[/{MODAL_GREEN}]")

    deployment_mode = questionary.select(
        "Choose deployment mode:",
        choices=[
            {"name": "🌱 Minimum - Fast CPU-only deployment", "value": "minimum"},
            {"name": "⚡ Optimized - GPU + ML libraries", "value": "optimized"},
            {"name": "📓 Marimo - Reactive notebooks + Gradio", "value": "marimo"},
            {"name": "🪐 Gradio-Jupyter - Classic notebooks + Gradio", "value": "gradio-jupyter"},
        ],
    ).ask()

    # Step 3: Infrastructure features
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]🏗️ Passo 3: Recursos de Infraestrutura[/{MODAL_GREEN}]")
    else:
        rprint(f"\n[{MODAL_GREEN}]🏗️ Step 3: Infrastructure Features[/{MODAL_GREEN}]")

    provision_nfs = questionary.confirm("Add persistent storage (NFS)?", default=False).ask()

    provision_logging = questionary.confirm("Add structured logging?", default=True).ask()

    enable_dashboard = questionary.confirm("Enable monitoring dashboard?", default=True).ask()

    # Step 4: GPU configuration (for optimized/marimo modes)
    gpu_type = None
    num_gpus = 0
    if deployment_mode in ["optimized", "marimo"]:
        if br_huehuehue:
            rprint(f"\n[{MODAL_GREEN}]🚀 Passo 4: Configuração de GPU[/{MODAL_GREEN}]")
        else:
            rprint(f"\n[{MODAL_GREEN}]🚀 Step 4: GPU Configuration[/{MODAL_GREEN}]")

        enable_gpu = questionary.confirm("Enable GPU support?", default=True).ask()

        if enable_gpu:
            gpu_type = questionary.select("Select GPU type:", choices=["any", "T4", "L4", "A10G", "A100", "H100"], default="any").ask()

            num_gpus = int(questionary.text("Number of GPUs:", default="1", validate=lambda x: x.isdigit() and int(x) > 0).ask())

    # Step 5: Dependencies
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]📦 Passo 5: Dependências[/{MODAL_GREEN}]")
    else:
        rprint(f"\n[{MODAL_GREEN}]📦 Step 5: Dependencies[/{MODAL_GREEN}]")

    # Check for requirements.txt
    requirements_file = None
    drop_folder = Path("drop-ur-precious-stuff-here")
    requirements_path = drop_folder / "requirements.txt"

    if requirements_path.exists():
        rprint(f"[{MODAL_LIGHT_GREEN}]Found requirements.txt in {drop_folder}![/{MODAL_LIGHT_GREEN}]")
        use_requirements = questionary.confirm("Use this requirements.txt?", default=True).ask()
        if use_requirements:
            requirements_file = requirements_path

    # System dependencies
    system_dependencies = []
    add_system_dep = questionary.confirm("Add system dependencies (apt packages)?", default=False).ask()

    while add_system_dep:
        dep = questionary.text("System dependency name:").ask()
        if dep:
            system_dependencies.append(dep)
        add_system_dep = questionary.confirm("Add another system dependency?", default=False).ask()

    # Python dependencies (in addition to requirements.txt)
    python_dependencies = []
    if provision_logging and "loguru" not in str(requirements_file.read_text() if requirements_file else ""):
        python_dependencies.append("loguru")

    add_python_dep = questionary.confirm("Add additional Python dependencies?", default=False).ask()

    while add_python_dep:
        dep = questionary.text("Python package name:").ask()
        if dep:
            python_dependencies.append(dep)
        add_python_dep = questionary.confirm("Add another Python dependency?", default=False).ask()

    # Step 6: Remote functions
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]🔧 Passo 6: Funções Remotas[/{MODAL_GREEN}]")
    else:
        rprint(f"\n[{MODAL_GREEN}]🔧 Step 6: Remote Functions[/{MODAL_GREEN}]")

    remote_functions = []
    add_remote_func = questionary.confirm("Add remote functions (background tasks, scheduled jobs)?", default=False).ask()

    while add_remote_func:
        func_name = questionary.text("Function name:", validate=lambda x: x.isidentifier() if x else False).ask()

        if not func_name:
            break

        func_config = {"name": func_name}

        # Keep warm configuration
        keep_warm = questionary.confirm(f"Keep {func_name} warm?", default=False).ask()

        if keep_warm:
            instances = questionary.text("Number of warm instances:", default="1", validate=lambda x: x.isdigit() and int(x) > 0).ask()
            func_config["keep_warm"] = int(instances)

        # GPU for function
        func_gpu = questionary.confirm(f"Enable GPU for {func_name}?", default=False).ask()

        if func_gpu:
            func_config["gpu"] = questionary.select("GPU type:", choices=["any", "T4", "L4", "A10G", "A100", "H100"], default="any").ask()

            func_config["num_gpus"] = int(
                questionary.text("Number of GPUs:", default="1", validate=lambda x: x.isdigit() and int(x) > 0).ask()
            )

        # Volume mount
        if provision_nfs:
            mount_volume = questionary.confirm(f"Mount persistent storage for {func_name}?", default=False).ask()
            if mount_volume:
                func_config["volume"] = {"/workspace": "volume"}

        # Secret
        use_secret = questionary.confirm(f"Add secret for {func_name}?", default=False).ask()

        if use_secret:
            secret_name = questionary.text("Secret name:").ask()
            if secret_name:
                func_config["secret"] = secret_name

        # Schedule (cron)
        use_schedule = questionary.confirm(f"Schedule {func_name} (cron)?", default=False).ask()

        if use_schedule:
            schedule = questionary.text("Cron schedule (e.g., '0 */6 * * *' for every 6 hours):").ask()
            if schedule:
                func_config["schedule"] = schedule

        remote_functions.append(func_config)

        add_remote_func = questionary.confirm("Add another remote function?", default=False).ask()

    # Step 7: Environment and secrets
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]🔐 Passo 7: Ambiente e Segredos[/{MODAL_GREEN}]")
    else:
        rprint(f"\n[{MODAL_GREEN}]🔐 Step 7: Environment and Secrets[/{MODAL_GREEN}]")

    environment_variables = {}
    add_env_var = questionary.confirm("Add environment variables?", default=False).ask()

    while add_env_var:
        key = questionary.text("Variable name:").ask()
        if key:
            value = questionary.text(f"Value for {key}:").ask()
            if value:
                environment_variables[key] = value

        add_env_var = questionary.confirm("Add another environment variable?", default=False).ask()

    secrets = []
    add_secret = questionary.confirm("Add Modal secrets?", default=False).ask()

    while add_secret:
        secret = questionary.text("Secret name:").ask()
        if secret:
            secrets.append(secret)

        add_secret = questionary.confirm("Add another secret?", default=False).ask()

    # Step 8: Advanced settings
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]⚙️ Passo 8: Configurações Avançadas[/{MODAL_GREEN}]")
    else:
        rprint(f"\n[{MODAL_GREEN}]⚙️ Step 8: Advanced Settings[/{MODAL_GREEN}]")

    timeout_minutes = int(questionary.text("Timeout in minutes:", default="60", validate=lambda x: x.isdigit() and int(x) > 0).ask())

    max_containers = int(questionary.text("Maximum containers:", default="10", validate=lambda x: x.isdigit() and int(x) > 0).ask())

    min_containers = int(questionary.text("Minimum containers:", default="1", validate=lambda x: x.isdigit() and int(x) >= 0).ask())

    # Summary
    if br_huehuehue:
        rprint(f"\n[{MODAL_GREEN}]📋 Resumo do Deployment[/{MODAL_GREEN}]")
    else:
        rprint(f"\n[{MODAL_GREEN}]📋 Deployment Summary[/{MODAL_GREEN}]")

    rprint(f"  📱 App: {app_name}")
    rprint(f"  ⚡ Mode: {deployment_mode.upper()}")
    rprint(f"  💾 Persistent Storage: {'YES' if provision_nfs else 'NO'}")
    rprint(f"  📊 Dashboard: {'YES' if enable_dashboard else 'NO'}")
    if gpu_type:
        rprint(f"  🚀 GPU: {gpu_type} x{num_gpus}")
    rprint(f"  🔧 Remote Functions: {len(remote_functions)}")
    rprint(f"  📦 Python Dependencies: {len(python_dependencies) + (1 if requirements_file else 0)}")
    rprint(f"  🔐 Secrets: {len(secrets)}")
    rprint(f"  ⏱️ Timeout: {timeout_minutes} minutes")
    rprint(f"  📈 Containers: {min_containers}-{max_containers}")

    if br_huehuehue:
        confirm = questionary.confirm("\nTudo certo? Vamos gerar o deployment! 🚀", default=True).ask()
    else:
        confirm = questionary.confirm("\nLooks good? Let's generate the deployment! 🚀", default=True).ask()

    if not confirm:
        return None

    # Generate deployment using new template system
    try:
        deployment_code = generate_from_wizard_input(
            app_name=app_name,
            deployment_mode=deployment_mode,
            original_code=original_code,
            provision_nfs=provision_nfs,
            provision_logging=provision_logging,
            system_dependencies=system_dependencies,
            python_dependencies=python_dependencies,
            remote_functions=remote_functions,
            gpu_type=gpu_type,
            secrets=secrets,
            environment_variables=environment_variables,
            requirements_file=requirements_file,
        )

        return deployment_code

    except Exception as e:
        logger.error(f"Failed to generate deployment: {e}")
        rprint(f"[red]Error generating deployment: {e}[/red]")
        return None


def add_enhanced_cli_commands(app: typer.Typer):
    """Add enhanced CLI commands to the main app."""

    @app.command()
    def generate(
        app_file: Annotated[Path, typer.Argument(help="Path to your Gradio app file")],
        output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file path")] = None,
        wizard: Annotated[bool, typer.Option("--wizard", "-w", help="Use advanced interactive wizard")] = True,
        br_huehuehue: Annotated[bool, typer.Option("--br-huehuehue", help="Modo brasileiro! 🇧🇷", hidden=True)] = False,
    ):
        """Generate advanced Modal deployment with all features.

        This command provides access to all modal_generate features including:
        - Remote functions with GPU, scheduling, and secrets
        - Persistent storage (NFS)
        - Environment variables and Modal secrets
        - System and Python dependencies
        - Advanced container configuration
        - Monitoring and logging
        """
        if not app_file.exists():
            rprint(f"[red]File not found: {app_file}[/red]")
            raise typer.Exit(1)

        if wizard:
            deployment_code = enhanced_wizard(app_file, br_huehuehue)
            if not deployment_code:
                rprint("[yellow]Deployment generation cancelled[/yellow]")
                raise typer.Exit(0)
        else:
            # Use basic configuration for non-wizard mode
            try:
                original_code = app_file.read_text()
                deployment_code = generate_from_wizard_input(
                    app_name=slugify(app_file.stem),
                    deployment_mode="minimum",
                    original_code=original_code,
                )
            except Exception as e:
                rprint(f"[red]Error generating deployment: {e}[/red]")
                raise typer.Exit(1)

        # Write output
        if output:
            output_path = output
        else:
            output_path = app_file.parent / f"modal_{app_file.name}"

        try:
            output_path.write_text(deployment_code)
            rprint(f"[green]✅ Deployment generated: {output_path}[/green]")
            rprint(f"[{MODAL_LIGHT_GREEN}]Run: modal deploy {output_path}[/{MODAL_LIGHT_GREEN}]")
        except Exception as e:
            rprint(f"[red]Error writing deployment file: {e}[/red]")
            raise typer.Exit(1)
