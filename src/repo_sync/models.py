"""Data models for repository synchronization."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Platform(Enum):
    """Supported Git hosting platforms."""

    GITHUB = "github"
    GITLAB = "gitlab"
    GITEA = "gitea"
    GITEE = "gitee"
    BITBUCKET = "bitbucket"


@dataclass
class PlatformConfig:
    """Configuration for a Git hosting platform."""

    platform: Platform
    url: str = ""
    token: str = ""

    def __post_init__(self):
        if isinstance(self.platform, str):
            self.platform = Platform(self.platform)

    @property
    def base_url(self) -> str:
        """Get the base URL for the platform."""
        if self.url:
            return self.url.rstrip("/")

        default_urls = {
            Platform.GITHUB: "https://github.com",
            Platform.GITLAB: "https://gitlab.com",
            Platform.GITEE: "https://gitee.com",
            Platform.GITEA: "http://localhost:3000",
            Platform.BITBUCKET: "https://bitbucket.org",
        }
        return default_urls.get(self.platform, "")


@dataclass
class Repository:
    """Information about a repository."""

    platform: Platform
    owner: str
    name: str
    clone_url: str = ""
    is_private: bool = False
    description: str = ""

    def __post_init__(self):
        if isinstance(self.platform, str):
            self.platform = Platform(self.platform)

    @property
    def full_name(self) -> str:
        """Get the full repository name (owner/name)."""
        return f"{self.owner}/{self.name}"


@dataclass
class SyncOptions:
    """Options for repository synchronization."""

    branches: Optional[List[str]] = None
    tags: bool = True
    private: bool = True
    auto_init: bool = False
    force: bool = False


@dataclass
class SyncTask:
    """A synchronization task definition."""

    name: str
    source: Repository
    targets: List[Repository]
    options: SyncOptions = field(default_factory=SyncOptions)

    def __post_init__(self):
        if isinstance(self.options, dict):
            self.options = SyncOptions(**self.options)


@dataclass
class SchedulerConfig:
    """Configuration for scheduled synchronization."""

    enabled: bool = False
    interval: str = "8h"

    def get_interval_seconds(self) -> int:
        """Convert interval string to seconds."""
        interval = self.interval.strip().lower()
        if interval.endswith("h"):
            return int(interval[:-1]) * 3600
        elif interval.endswith("m"):
            return int(interval[:-1]) * 60
        elif interval.endswith("d"):
            return int(interval[:-1]) * 86400
        return int(interval)


@dataclass
class WebhookConfig:
    """Configuration for webhook server."""

    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    secret: str = ""


@dataclass
class AppConfig:
    """Main application configuration."""

    version: str = "1.0"
    platforms: dict = field(default_factory=dict)
    sync_tasks: List[SyncTask] = field(default_factory=list)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    webhook: WebhookConfig = field(default_factory=WebhookConfig)

    def get_platform_config(self, platform: Platform) -> Optional[PlatformConfig]:
        """Get platform configuration by platform type."""
        platform_key = platform.value
        if platform_key in self.platforms:
            config_data = self.platform[platform_key]
            return PlatformConfig(
                platform=platform,
                url=config_data.get("url", ""),
                token=config_data.get("token", ""),
            )
        return None
