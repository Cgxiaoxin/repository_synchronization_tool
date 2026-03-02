"""Platform adapters for different Git hosting services."""

from .base import BasePlatform
from .github import GitHubPlatform
from .gitlab import GitLabPlatform
from .gitea import GiteaPlatform
from .gitee import GiteePlatform
from ..models import Platform, PlatformConfig


PLATFORM_ADAPTERS = {
    Platform.GITHUB: GitHubPlatform,
    Platform.GITLAB: GitLabPlatform,
    Platform.GITEA: GiteaPlatform,
    Platform.GITEE: GiteePlatform,
}


def get_platform_adapter(platform: Platform, config: PlatformConfig) -> BasePlatform:
    """Get the appropriate platform adapter."""
    adapter_class = PLATFORM_ADAPTERS.get(platform)
    if adapter_class is None:
        raise ValueError(f"Unsupported platform: {platform}")
    return adapter_class(config)


__all__ = [
    "BasePlatform",
    "GitHubPlatform",
    "GitLabPlatform",
    "GiteaPlatform",
    "GiteePlatform",
    "get_platform_adapter",
    "PLATFORM_ADAPTERS",
]
