"""Authentication and installation helpers for modal-for-noobs CLI."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger
from rich import print as rprint

from modal_for_noobs.cli_helpers.common import MODAL_GREEN, MODAL_LIGHT_GREEN, print_error, print_success, print_warning


async def setup_auth_async(token_id: str | None, token_secret: str | None, br_huehuehue: bool = False) -> None:
    """Async authentication setup with progress."""
    from modal_for_noobs.modal_deploy import ModalDeployer

    deployer = ModalDeployer(app_file=Path("dummy"), mode="minimum")

    if token_id and token_secret:
        os.environ["MODAL_TOKEN_ID"] = token_id
        os.environ["MODAL_TOKEN_SECRET"] = token_secret
        if br_huehuehue:
            print_success("Autenticação Modal configurada via variáveis de ambiente! Huehuehue!")
        else:
            print_success("Modal authentication configured via environment variables!")
    else:
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn

        console = Console()

        with Progress(
            SpinnerColumn(spinner_name="dots", style=f"{MODAL_GREEN}"),
            TextColumn("[progress.description]{task.description}", style="bold white"),
            console=console,
        ) as progress:
            if br_huehuehue:
                auth_task = progress.add_task("🔐 Configurando autenticação Modal... Huehuehue!", total=None)
            else:
                auth_task = progress.add_task("🔐 Setting up Modal authentication...", total=None)

            success = await deployer.setup_modal_auth_async()

            if success:
                progress.update(auth_task, description="✅ Authentication setup complete!")
                if br_huehuehue:
                    print_success("Tudo pronto! Agora você pode deployar! Huehuehue! 🚀")
                else:
                    print_success("You're all set! Ready to deploy! 🚀")
            else:
                progress.update(auth_task, description="❌ Authentication failed!")
                if br_huehuehue:
                    print_error("Falha na configuração da autenticação!")
                else:
                    print_error("Authentication setup failed!")


def install_mn_alias(shell: str | None, force: bool, br_huehuehue: bool) -> bool:
    """Install the 'mn' alias globally for the current shell.

    Args:
        shell: Shell type (bash, zsh, fish) or None for auto-detect
        force: Whether to force overwrite existing alias
        br_huehuehue: Brazilian mode

    Returns:
        bool: True if installation succeeded, False otherwise
    """
    try:
        # Detect current shell if not specified
        if shell is None:
            shell_env = os.environ.get("SHELL", "")
            if "zsh" in shell_env:
                shell = "zsh"
            elif "bash" in shell_env:
                shell = "bash"
            elif "fish" in shell_env:
                shell = "fish"
            else:
                shell = "bash"  # Default fallback

        if br_huehuehue:
            rprint(f"[{MODAL_LIGHT_GREEN}]🐚 Shell detectado: {shell}[/{MODAL_LIGHT_GREEN}]")
        else:
            rprint(f"[{MODAL_LIGHT_GREEN}]🐚 Detected shell: {shell}[/{MODAL_LIGHT_GREEN}]")

        # Get the current Python executable and modal-for-noobs module path
        python_executable = shutil.which("python") or shutil.which("python3")
        if not python_executable:
            print_error("Python executable not found in PATH")
            return False

        # Try to find modal-for-noobs in the current environment
        try:
            result = subprocess.run(
                [python_executable, "-c", "import modal_for_noobs; print(modal_for_noobs.__file__)"],
                capture_output=True,
                text=True,
                check=True,
            )
            module_path = Path(result.stdout.strip()).parent
        except subprocess.CalledProcessError:
            # Fallback: use the current source path if we're in development
            module_path = Path(__file__).parent.parent

        # Determine shell configuration file
        home = Path.home()

        if shell == "zsh":
            shell_config = home / ".zshrc"
            alias_line = f'''# mn - Modal-for-noobs global function
mn() {{
    "{python_executable}" -m modal_for_noobs.cli "$@"
}}'''
        elif shell == "bash":
            # Try .bashrc first, then .bash_profile
            shell_config = home / ".bashrc"
            if not shell_config.exists():
                shell_config = home / ".bash_profile"
            alias_line = f'''# mn - Modal-for-noobs global function
mn() {{
    "{python_executable}" -m modal_for_noobs.cli "$@"
}}'''
        elif shell == "fish":
            shell_config = home / ".config" / "fish" / "config.fish"
            shell_config.parent.mkdir(parents=True, exist_ok=True)
            alias_line = f'''# mn - Modal-for-noobs global function
function mn
    "{python_executable}" -m modal_for_noobs.cli $argv
end'''
        else:
            print_error(f"Unsupported shell: {shell}")
            return False

        # Check if alias/function already exists
        if shell_config.exists():
            content = shell_config.read_text()
            if "alias mn=" in content or "alias mn '" in content or "mn()" in content or "function mn" in content:
                if not force:
                    if br_huehuehue:
                        print_warning("Comando 'mn' já existe! Use --force para sobrescrever.")
                    else:
                        print_warning("Command 'mn' already exists! Use --force to overwrite.")
                    return False

                # Remove existing mn alias/function lines
                lines = content.split("\n")
                new_lines = []
                in_mn_function = False
                for line in lines:
                    if (
                        "# mn - Modal-for-noobs" in line
                        or line.strip().startswith("alias mn=")
                        or line.strip().startswith("alias mn '")
                        or line.strip().startswith("mn()")
                        or line.strip().startswith("function mn")
                    ):
                        in_mn_function = True
                        continue
                    elif in_mn_function and (line.strip() == "}" or line.strip() == "end"):
                        in_mn_function = False
                        continue
                    elif not in_mn_function:
                        new_lines.append(line)
                content = "\n".join(new_lines)
        else:
            content = ""

        # Add the new function
        if content and not content.endswith("\n"):
            content += "\n"

        content += f"""
# mn - Modal-for-noobs global function (added by modal-for-noobs install-alias)
{alias_line}
"""

        # Write the updated configuration
        shell_config.write_text(content)

        if br_huehuehue:
            rprint(f"[{MODAL_GREEN}]✅ Função 'mn' adicionada a {shell_config}[/{MODAL_GREEN}]")
            rprint(f"[{MODAL_LIGHT_GREEN}]💡 Execute 'source {shell_config}' ou abra um novo terminal[/{MODAL_LIGHT_GREEN}]")
        else:
            rprint(f"[{MODAL_GREEN}]✅ Function 'mn' added to {shell_config}[/{MODAL_GREEN}]")
            rprint(f"[{MODAL_LIGHT_GREEN}]💡 Run 'source {shell_config}' or open a new terminal[/{MODAL_LIGHT_GREEN}]")

        return True

    except Exception as e:
        logger.error(f"Error installing mn alias: {e}")
        return False
