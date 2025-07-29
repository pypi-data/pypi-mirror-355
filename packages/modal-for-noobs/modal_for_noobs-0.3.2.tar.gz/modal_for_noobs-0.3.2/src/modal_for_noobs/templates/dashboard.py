"""Modal deployment dashboard template.

This module provides a Gradio dashboard interface for monitoring and managing
Modal deployments. It includes logging, metrics, and deployment information.
"""

import asyncio
import json
import os
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import gradio as gr
import modal
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

# Import Modal UI components and themes
try:
    from modal_for_noobs.ui.themes import MODAL_CSS, MODAL_THEME
except ImportError:
    # Fallback if running standalone
    MODAL_THEME = gr.themes.Soft()
    MODAL_CSS = ""


class LogEntry(BaseModel):
    """Model for log entries."""

    timestamp: str
    level: str
    message: str
    extra: dict[str, Any] | None = None


class DeploymentInfo(BaseModel):
    """Model for deployment information."""

    app_name: str
    deployment_mode: str
    deployment_time: str
    modal_version: str
    python_version: str
    gpu_enabled: bool
    timeout_seconds: int
    max_containers: int
    environment: dict[str, str]


class DashboardState:
    """Manages dashboard state and logging."""

    def __init__(self, max_logs: int = 1000):
        self.logs: deque[LogEntry] = deque(maxlen=max_logs)
        self.deployment_info: DeploymentInfo | None = None
        self.start_time = datetime.now()
        self._setup_logging()

    def _setup_logging(self):
        """Configure loguru to capture logs."""
        # Remove default handler
        logger.remove()

        # Add custom handler that stores logs in memory
        logger.add(
            self._log_handler, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="DEBUG", backtrace=True, diagnose=True
        )

        # Also log to stdout for Modal logs
        logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}", level="INFO")

    def _log_handler(self, message):
        """Custom log handler that stores logs in memory."""
        record = message.record
        log_entry = LogEntry(
            timestamp=record["time"].strftime("%Y-%m-%d %H:%M:%S"),
            level=record["level"].name,
            message=record["message"],
            extra=record.get("extra", {}),
        )
        self.logs.append(log_entry)

    def get_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get the most recent logs."""
        logs_list = list(self.logs)
        if limit > 0:
            logs_list = logs_list[-limit:]
        return [log.dict() for log in logs_list]

    def get_deployment_info(self) -> dict[str, Any]:
        """Get deployment information."""
        if self.deployment_info:
            return self.deployment_info.dict()
        return {}

    def set_deployment_info(self, info: DeploymentInfo):
        """Set deployment information."""
        self.deployment_info = info
        logger.info(f"Deployment info set: {info.app_name} ({info.deployment_mode})")


# Global dashboard state
dashboard_state = DashboardState()


def create_dashboard_interface(app_demo: gr.Interface) -> gr.Blocks:
    """Create the dashboard interface with tabs for app and monitoring.

    Args:
        app_demo: The original Gradio interface/blocks to embed

    Returns:
        gr.Blocks: The complete dashboard interface
    """
    with gr.Blocks(title="Modal Deployment Dashboard", theme=MODAL_THEME, css=MODAL_CSS) as dashboard:
        gr.Markdown("# 🚀 Modal Deployment Dashboard")
        gr.Markdown("Monitor and manage your Modal deployment")

        with gr.Tabs():
            # Main App Tab
            with gr.Tab("📱 Application"):
                gr.Markdown("### Your Deployed Application")
                # Embed the original app
                if hasattr(app_demo, "render"):
                    app_demo.render()
                else:
                    gr.Markdown("⚠️ Application interface could not be rendered")

            # Logs Tab
            with gr.Tab("📋 Logs"):
                gr.Markdown("### Application Logs")

                with gr.Row():
                    log_limit = gr.Number(value=100, label="Log Limit", minimum=10, maximum=1000)
                    refresh_btn = gr.Button("🔄 Refresh Logs", variant="primary")
                    clear_btn = gr.Button("🗑️ Clear Logs", variant="secondary")

                log_output = gr.JSON(label="Recent Logs", height=600)

                def refresh_logs(limit):
                    logs = dashboard_state.get_logs(int(limit))
                    logger.info(f"Refreshed logs view (showing {len(logs)} entries)")
                    return logs

                def clear_logs():
                    dashboard_state.logs.clear()
                    logger.info("Logs cleared")
                    return []

                refresh_btn.click(refresh_logs, inputs=[log_limit], outputs=[log_output])
                clear_btn.click(clear_logs, outputs=[log_output])

                # Auto-refresh logs every 5 seconds
                dashboard.load(refresh_logs, inputs=[log_limit], outputs=[log_output])

            # Deployment Info Tab
            with gr.Tab("ℹ️ Deployment Info"):
                gr.Markdown("### Deployment Configuration")
                deployment_info = gr.JSON(label="Deployment Information", value=dashboard_state.get_deployment_info())

                refresh_info_btn = gr.Button("🔄 Refresh Info", variant="primary")

                def refresh_deployment_info():
                    info = dashboard_state.get_deployment_info()
                    logger.info("Refreshed deployment info")
                    return info

                refresh_info_btn.click(refresh_deployment_info, outputs=[deployment_info])

            # Metrics Tab
            with gr.Tab("📊 Metrics"):
                gr.Markdown("### Runtime Metrics")

                with gr.Row():
                    uptime = gr.Textbox(label="Uptime", interactive=False)
                    log_count = gr.Number(label="Total Logs", interactive=False)
                    memory_usage = gr.Textbox(label="Memory Usage", interactive=False)

                def get_metrics():
                    import psutil

                    uptime_seconds = (datetime.now() - dashboard_state.start_time).total_seconds()
                    hours, remainder = divmod(uptime_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024

                    return uptime_str, len(dashboard_state.logs), f"{memory_mb:.2f} MB"

                metrics_btn = gr.Button("📊 Update Metrics", variant="primary")
                metrics_btn.click(get_metrics, outputs=[uptime, log_count, memory_usage])

                # Auto-refresh metrics every 10 seconds
                dashboard.load(get_metrics, outputs=[uptime, log_count, memory_usage])

        gr.Markdown("---")
        gr.Markdown("🚀 Powered by [Modal](https://modal.com) | Generated by [modal-for-noobs](https://github.com/arthrod/modal-for-noobs)")

    return dashboard


def create_dashboard_api(fastapi_app: FastAPI) -> FastAPI:
    """Add dashboard API endpoints to the FastAPI app.

    Args:
        fastapi_app: The FastAPI application instance

    Returns:
        FastAPI: The enhanced FastAPI app with dashboard endpoints
    """

    @fastapi_app.get("/api/logs")
    async def get_logs(limit: int = 100):
        """Get application logs."""
        try:
            logs = dashboard_state.get_logs(limit)
            return {"status": "success", "logs": logs, "count": len(logs)}
        except Exception as e:
            logger.error(f"Error fetching logs: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @fastapi_app.get("/api/deployment-info")
    async def get_deployment_info():
        """Get deployment information."""
        try:
            info = dashboard_state.get_deployment_info()
            return {"status": "success", "info": info}
        except Exception as e:
            logger.error(f"Error fetching deployment info: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @fastapi_app.get("/api/metrics")
    async def get_metrics():
        """Get runtime metrics."""
        try:
            import psutil

            process = psutil.Process()

            uptime_seconds = (datetime.now() - dashboard_state.start_time).total_seconds()

            metrics = {
                "uptime_seconds": uptime_seconds,
                "log_count": len(dashboard_state.logs),
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(interval=0.1),
                "num_threads": process.num_threads(),
            }

            return {"status": "success", "metrics": metrics}
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @fastapi_app.post("/api/logs/clear")
    async def clear_logs():
        """Clear all logs."""
        try:
            dashboard_state.logs.clear()
            logger.info("Logs cleared via API")
            return {"status": "success", "message": "Logs cleared"}
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    logger.info("Dashboard API endpoints configured")
    return fastapi_app
