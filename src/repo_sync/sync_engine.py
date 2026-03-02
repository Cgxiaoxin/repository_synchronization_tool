"""Synchronization engine for repository synchronization."""

import logging
import os
from typing import List, Optional

from .config import ConfigManager
from .git_operator import GitOperator, GitError
from .models import Platform, PlatformConfig, Repository, SyncOptions, SyncTask
from .platforms import get_platform_adapter

logger = logging.getLogger(__name__)


class SyncResult:
    """Result of a synchronization operation."""

    def __init__(self, success: bool, message: str, details: Optional[dict] = None):
        self.success = success
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        return f"{'[SUCCESS]' if self.success else '[FAILED]'}: {self.message}"


class SyncEngine:
    """Engine for synchronizing repositories across platforms."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load()
        self.git = GitOperator()

    def _get_platform_config(self, platform: Platform) -> Optional[PlatformConfig]:
        """Get platform configuration."""
        token = self._get_token_from_env(platform)
        if token:
            platform_config = self.config.get_platform_config(platform)
            if platform_config:
                platform_config.token = token
                return platform_config
            return PlatformConfig(platform=platform, token=token)
        
        return self.config.get_platform_config(platform)

    def _get_token_from_env(self, platform: Platform) -> Optional[str]:
        """Get token from environment variable."""
        env_var = f"{platform.value.upper()}_TOKEN"
        return os.environ.get(env_var)

    def sync_task(self, task: SyncTask) -> List[SyncResult]:
        """Synchronize a single task."""
        results = []

        source_config = self._get_platform_config(task.source.platform)
        if not source_config or not source_config.token:
            results.append(SyncResult(False, f"No credentials for {task.source.platform.value}"))
            return results

        try:
            source_adapter = get_platform_adapter(task.source.platform, source_config)
        except ValueError as e:
            results.append(SyncResult(False, f"Unsupported platform: {e}"))
            return results

        source_repo = source_adapter.get_repo(task.source.owner, task.source.name)
        if not source_repo:
            results.append(SyncResult(False, f"Source repository {task.source.full_name} not found"))
            return results

        for target in task.targets:
            result = self._sync_to_target(source_repo, target, task.options)
            results.append(result)

        return results

    def _sync_to_target(self, source_repo: Repository, target: Repository, options: SyncOptions) -> SyncResult:
        """Synchronize from source to target repository."""
        target_config = self._get_platform_config(target.platform)
        if not target_config or not target_config.token:
            return SyncResult(False, f"No credentials for {target.platform.value}")

        source_config = self._get_platform_config(source_repo.platform)
        if not source_config or not source_config.token:
            return SyncResult(False, f"No credentials for {source_repo.platform.value}")

        try:
            source_adapter = get_platform_adapter(source_repo.platform, source_config)
            target_adapter = get_platform_adapter(target.platform, target_config)
        except ValueError as e:
            return SyncResult(False, f"Unsupported platform: {e}")

        if not target_adapter.repo_exists(target.owner, target.name):
            logger.info(f"Creating repository {target.full_name} on {target.platform.value}")
            new_repo = target_adapter.create_repo(
                name=target.name,
                private=options.private,
                description=source_repo.description,
                auto_init=options.auto_init,
            )
            if not new_repo:
                return SyncResult(False, f"Failed to create repository {target.full_name}")

        temp_dir = None
        try:
            temp_dir = GitOperator.get_temp_dir(f"sync_{source_repo.name}_")
            
            logger.info(f"Cloning {source_repo.full_name}...")
            self.git.clone_mirror(
                source_repo.clone_url,
                temp_dir,
                username=source_repo.owner,
                password=self._get_token_from_env(source_repo.platform),
            )

            target_clone_url = self._build_target_clone_url(target, target_config)
            
            logger.info(f"Pushing to {target.full_name}...")
            self.git.push_mirror(
                temp_dir,
                target_clone_url,
                username=target.owner,
                password=target_config.token,
            )

            if source_repo.platform == Platform.GITEA or source_repo.platform == Platform.GITLAB:
                target_url_with_auth = self._build_target_clone_url(target, target_config, include_auth=True)
                source_adapter.setup_push_mirror(
                    source_repo,
                    target_url_with_auth,
                    sync_on_commit=True,
                    interval="8h",
                )

            return SyncResult(
                True,
                f"Successfully synced {source_repo.full_name} to {target.full_name}",
                {"source": source_repo.full_name, "target": target.full_name},
            )

        except GitError as e:
            return SyncResult(False, f"Git error: {e}")
        except Exception as e:
            return SyncResult(False, f"Error: {e}")
        finally:
            if temp_dir:
                self.git.cleanup(temp_dir)

    def _build_target_clone_url(self, target: Repository, config: PlatformConfig, include_auth: bool = False) -> str:
        """Build the clone URL for target repository."""
        base_url = config.base_url
        
        if include_auth:
            return f"{base_url}/{target.owner}/{target.name}.git"
        
        return f"{base_url}/{target.owner}/{target.name}.git"

    def sync_all(self) -> List[SyncResult]:
        """Synchronize all configured tasks."""
        results = []
        for task in self.config.sync_tasks:
            logger.info(f"Syncing task: {task.name}")
            task_results = self.sync_task(task)
            results.extend(task_results)
        return results

    def sync_by_name(self, task_name: str) -> List[SyncResult]:
        """Synchronize a specific task by name."""
        task = self.config_manager.get_sync_task(task_name)
        if not task:
            return [SyncResult(False, f"Task '{task_name}' not found")]
        return self.sync_task(task)

    def add_task(self, task: SyncTask) -> bool:
        """Add a new sync task."""
        try:
            self.config_manager.add_sync_task(task)
            return True
        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            return False

    def remove_task(self, task_name: str) -> bool:
        """Remove a sync task."""
        return self.config_manager.remove_sync_task(task_name)

    def list_tasks(self) -> List[SyncTask]:
        """List all sync tasks."""
        return self.config.sync_tasks
