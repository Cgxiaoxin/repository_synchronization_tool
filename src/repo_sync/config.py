"""Configuration management for repository synchronization."""

import os
from pathlib import Path
from typing import Optional

import yaml

from .models import (
    AppConfig,
    Platform,
    Repository,
    SyncOptions,
    SyncTask,
    SchedulerConfig,
    WebhookConfig,
)


DEFAULT_CONFIG_FILE = "config.yaml"


class ConfigManager:
    """Manage application configuration."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self._config: Optional[AppConfig] = None

    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in current directory or home."""
        search_paths = [
            Path.cwd() / DEFAULT_CONFIG_FILE,
            Path.cwd() / ".repo-sync.yaml",
            Path.home() / ".repo-sync" / DEFAULT_CONFIG_FILE,
            Path.home() / ".config" / "repo-sync" / DEFAULT_CONFIG_FILE,
        ]

        for path in search_paths:
            if path.exists():
                return str(path)

        return str(Path.cwd() / DEFAULT_CONFIG_FILE)

    def load(self) -> AppConfig:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            self._config = AppConfig()
            return self._config

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self._config = self._parse_config(data)
        return self._config

    def _parse_config(self, data: dict) -> AppConfig:
        """Parse configuration data into AppConfig."""
        sync_tasks = []
        for task_data in data.get("sync_tasks", []):
            source_data = task_data.get("source", {})
            targets_data = task_data.get("targets", [])

            source = Repository(
                platform=Platform(source_data.get("platform", "gitea")),
                owner=source_data.get("owner", ""),
                name=source_data.get("repo", ""),
                clone_url=source_data.get("clone_url", ""),
                is_private=source_data.get("private", False),
                description=source_data.get("description", ""),
            )

            targets = []
            for target_data in targets_data:
                target = Repository(
                    platform=Platform(target_data.get("platform", "github")),
                    owner=target_data.get("owner", ""),
                    name=target_data.get("repo", source.name),
                    is_private=target_data.get("private", True),
                )
                targets.append(target)

            options = SyncOptions(
                branches=task_data.get("options", {}).get("branches"),
                tags=task_data.get("options", {}).get("tags", True),
                private=task_data.get("options", {}).get("private", True),
                auto_init=task_data.get("options", {}).get("auto_init", False),
            )

            sync_tasks.append(
                SyncTask(
                    name=task_data.get("name", source.name),
                    source=source,
                    targets=targets,
                    options=options,
                )
            )

        scheduler_data = data.get("scheduler", {})
        webhook_data = data.get("webhook", {})

        return AppConfig(
            version=data.get("version", "1.0"),
            platforms=data.get("platforms", {}),
            sync_tasks=sync_tasks,
            scheduler=SchedulerConfig(
                enabled=scheduler_data.get("enabled", False),
                interval=scheduler_data.get("interval", "8h"),
            ),
            webhook=WebhookConfig(
                enabled=webhook_data.get("enabled", False),
                host=webhook_data.get("host", "0.0.0.0"),
                port=webhook_data.get("port", 8080),
                secret=webhook_data.get("secret", ""),
            ),
        )

    def save(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to file."""
        if config is None:
            config = self._config

        if config is None:
            return

        data = {
            "version": config.version,
            "platforms": config.platforms,
            "sync_tasks": [],
            "scheduler": {
                "enabled": config.scheduler.enabled,
                "interval": config.scheduler.interval,
            },
            "webhook": {
                "enabled": config.webhook.enabled,
                "host": config.webhook.host,
                "port": config.webhook.port,
                "secret": config.webhook.secret,
            },
        }

        for task in config.sync_tasks:
            task_dict = {
                "name": task.name,
                "source": {
                    "platform": task.source.platform.value,
                    "owner": task.source.owner,
                    "repo": task.source.name,
                    "private": task.source.is_private,
                },
                "targets": [],
                "options": {
                    "tags": task.options.tags,
                    "private": task.options.private,
                    "auto_init": task.options.auto_init,
                },
            }

            if task.options.branches:
                task_dict["options"]["branches"] = task.options.branches

            for target in task.targets:
                target_dict = {
                    "platform": target.platform.value,
                    "owner": target.owner,
                    "repo": target.name,
                }
                task_dict["targets"].append(target_dict)

            data["sync_tasks"].append(task_dict)

        os.makedirs(os.path.dirname(self.config_path) or ".", exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    @property
    def config(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            self._config = self.load()
        return self._config

    def add_sync_task(self, task: SyncTask) -> None:
        """Add a new sync task."""
        self.config.sync_tasks.append(task)
        self.save()

    def remove_sync_task(self, task_name: str) -> bool:
        """Remove a sync task by name."""
        for i, task in enumerate(self.config.sync_tasks):
            if task.name == task_name:
                self.config.sync_tasks.pop(i)
                self.save()
                return True
        return False

    def get_sync_task(self, task_name: str) -> Optional[SyncTask]:
        """Get a sync task by name."""
        for task in self.config.sync_tasks:
            if task.name == task_name:
                return task
        return None


def get_default_config_template() -> str:
    """Get default configuration template."""
    return '''# Repository Synchronization Tool Configuration
# Version 1.0

# Platform credentials
# Note: Tokens can also be set via environment variables:
#   - GITHUB_TOKEN, GITLAB_TOKEN, GITEA_TOKEN, GITEE_TOKEN, BITBUCKET_TOKEN
platforms:
  github:
    # url: "https://api.github.com"  # For GitHub Enterprise
    token: "your-github-token"
  
  gitlab:
    # url: "https://gitlab.com"  # For self-hosted GitLab
    token: "your-gitlab-token"
  
  gitea:
    url: "http://gitea.example.com"
    token: "your-gitea-token"
  
  gitee:
    token: "your-gitee-token"

# Synchronization tasks
sync_tasks:
  - name: "my-project"
    source:
      platform: "gitea"
      owner: "username"
      repo: "my-project"
    targets:
      - platform: "github"
        owner: "username"
      - platform: "gitlab"
        owner: "username"
    options:
      # branches: ["main", "develop"]  # Sync specific branches (empty = all)
      tags: true
      private: true
      auto_init: false

# Scheduled synchronization
scheduler:
  enabled: false
  interval: "8h"  # Format: "8h", "30m", "1d"

# Webhook server
webhook:
  enabled: false
  host: "0.0.0.0"
  port: 8080
  # secret: "your-webhook-secret"  # For signature verification
'''
