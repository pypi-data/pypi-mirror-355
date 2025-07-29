"""Logs management helpers for modal-for-noobs CLI."""

import asyncio
from pathlib import Path

from rich import print as rprint

from modal_for_noobs.cli_helpers.common import MODAL_GREEN, MODAL_LIGHT_GREEN, print_error, print_info, print_success, print_warning


async def milk_logs_async(app_name: str | None = None, follow: bool = False, lines: int = 100, br_huehuehue: bool = False) -> None:
    """Async log milking functionality - get those creamy logs! 🥛."""
    from modal_for_noobs.modal_deploy import ModalDeployer

    deployer = ModalDeployer(app_file=Path("dummy"), mode="minimum")

    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn

    console = Console()

    with Progress(
        SpinnerColumn(spinner_name="dots", style=f"{MODAL_GREEN}"),
        TextColumn("[progress.description]{task.description}", style="bold white"),
        console=console,
    ) as progress:
        # Check authentication first
        auth_task = progress.add_task("🔍 Checking Modal authentication...", total=None)

        if not await deployer.check_modal_auth_async():
            progress.update(auth_task, description="❌ No Modal authentication found!")
            if br_huehuehue:
                print_error("Nenhuma autenticação Modal encontrada! Huehuehue, configure primeiro!")
            else:
                print_error("No Modal authentication found! Please run 'modal-for-noobs auth' first!")
            return

        progress.update(auth_task, description="✅ Authentication verified!")

        if not app_name:
            # List apps for user to choose
            list_task = progress.add_task("📋 Finding apps to milk logs from...", total=None)

            try:
                process = await asyncio.create_subprocess_exec(
                    "modal", "app", "list", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                progress.update(list_task, description="✅ Apps found!")

                if process.returncode == 0:
                    output = stdout.decode().strip()
                    if output:
                        if br_huehuehue:
                            rprint(f"\n[{MODAL_GREEN}]🥛 Apps disponíveis para ordenhar logs (huehuehue!):[/{MODAL_GREEN}]")
                        else:
                            rprint(f"\n[{MODAL_GREEN}]🥛 Apps available for log milking:[/{MODAL_GREEN}]")
                        rprint(f"```\n{output}\n```")

                        if br_huehuehue:
                            rprint(f"\n[{MODAL_LIGHT_GREEN}]💡 Para ordenhar logs de um app específico:[/{MODAL_LIGHT_GREEN}]")
                            rprint("modal-for-noobs milk-logs <app-name> --br-huehuehue")
                        else:
                            rprint(f"\n[{MODAL_LIGHT_GREEN}]💡 To milk logs from a specific app:[/{MODAL_LIGHT_GREEN}]")
                            rprint("modal-for-noobs milk-logs <app-name> --follow")
                    else:
                        if br_huehuehue:
                            rprint(
                                f"\n[{MODAL_LIGHT_GREEN}]✨ Nenhum app para ordenhar! Deploye algo primeiro! Huehuehue![/{MODAL_LIGHT_GREEN}]"
                            )
                        else:
                            rprint(f"\n[{MODAL_LIGHT_GREEN}]✨ No apps to milk logs from! Deploy something first![/{MODAL_LIGHT_GREEN}]")
                else:
                    error_msg = stderr.decode().strip()
                    if br_huehuehue:
                        print_error(f"Erro ao listar apps: {error_msg}")
                    else:
                        print_error(f"Error listing apps: {error_msg}")

            except Exception as e:
                progress.update(list_task, description="❌ Error listing apps!")
                if br_huehuehue:
                    print_error(f"Erro ao listar apps: {str(e)}")
                else:
                    print_error(f"Error listing apps: {str(e)}")

        else:
            # Milk logs from specific app
            milk_task = progress.add_task(f"🥛 Milking logs from {app_name}...", total=None)

            try:
                # Build modal logs command - Modal CLI uses different syntax
                cmd = ["modal", "app", "logs", app_name]
                if follow:
                    cmd.append("--follow")

                # For non-follow mode, get all logs at once
                process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    progress.update(milk_task, description=f"✅ Logs milked from {app_name}!")

                    logs = stdout.decode().strip()
                    if logs:
                        if br_huehuehue:
                            rprint(f"\n[{MODAL_GREEN}]🥛 Logs fresquinhos de {app_name} (huehuehue!):[/{MODAL_GREEN}]")
                        else:
                            rprint(f"\n[{MODAL_GREEN}]🥛 Fresh creamy logs from {app_name}:[/{MODAL_GREEN}]")
                        rprint("=" * 80)

                        # Pretty print logs with milk emojis (limit to requested lines)
                        log_lines = logs.split("\n")
                        displayed_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines

                        for line in displayed_lines:
                            if line.strip():
                                rprint(f"🥛 {line}")

                        rprint("=" * 80)
                        if br_huehuehue:
                            print_success(f"Logs ordenhados com sucesso de {app_name}! ({len(displayed_lines)} linhas) Huehuehue!")
                        else:
                            print_success(f"Successfully milked {len(displayed_lines)} lines of creamy logs from {app_name}!")
                    else:
                        if br_huehuehue:
                            rprint(f"\n[{MODAL_LIGHT_GREEN}]📝 Nenhum log encontrado para {app_name}![/{MODAL_LIGHT_GREEN}]")
                        else:
                            rprint(f"\n[{MODAL_LIGHT_GREEN}]📝 No logs found for {app_name}![/{MODAL_LIGHT_GREEN}]")
                else:
                    error_msg = stderr.decode().strip()
                    progress.update(milk_task, description="❌ Failed to milk logs!")
                    if br_huehuehue:
                        print_error(f"Erro ao ordenhar logs: {error_msg}")
                    else:
                        print_error(f"Failed to milk logs: {error_msg}")

            except Exception as e:
                progress.update(milk_task, description="❌ Error during log milking!")
                if br_huehuehue:
                    print_error(f"Erro ao ordenhar logs: {str(e)}")
                else:
                    print_error(f"Error milking logs: {str(e)}")
