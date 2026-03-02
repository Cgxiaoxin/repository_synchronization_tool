"""Repository Synchronization Tool.

A CLI tool for synchronizing repositories across multiple Git hosting platforms.
Supports GitHub, GitLab, Gitea, Gitee, and more.
"""

from .cli import cli, main
from .config import ConfigManager, get_default_config_template
from .models import (
    Platform,
    PlatformConfig,
    Repository,
    SyncOptions,
    SyncTask,
    SchedulerConfig,
    WebhookConfig,
    AppConfig,
)
from .sync_engine import SyncEngine, SyncResult
from .scheduler import Scheduler, start_scheduler

__version__ = "0.1.0"

__all__ = [
    "cli",
    "main",
    "ConfigManager",
    "get_default_config_template",
    "Platform",
    "PlatformConfig",
    "Repository",
    "SyncOptions",
    "SyncTask",
    "SchedulerConfig",
    "WebhookConfig",
    "AppConfig",
    "SyncEngine",
    "SyncResult",
    "Scheduler",
    "start_scheduler",
]
