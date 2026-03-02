"""Base platform adapter interface."""

from abc import ABC, abstractmethod
from typing import Optional

import requests

from ..models import Platform, PlatformConfig, Repository


class BasePlatform(ABC):
    """Base class for platform adapters."""

    def __init__(self, config: PlatformConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(self._get_headers())

    @abstractmethod
    def _get_headers(self) -> dict:
        """Get headers for API requests."""
        pass

    @abstractmethod
    def _get_api_base_url(self) -> str:
        """Get the base URL for API requests."""
        pass

    @abstractmethod
    def _get_clone_url(self, owner: str, name: str) -> str:
        """Get the clone URL for a repository."""
        pass

    def get_repo(self, owner: str, name: str) -> Optional[Repository]:
        """Get repository information."""
        url = f"{self._get_api_base_url()}/repos/{owner}/{name}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return Repository(
                platform=self.config.platform,
                owner=owner,
                name=name,
                clone_url=data.get("clone_url", self._get_clone_url(owner, name)),
                is_private=data.get("private", False),
                description=data.get("description", ""),
            )
        except requests.RequestException:
            return None

    @abstractmethod
    def create_repo(
        self,
        name: str,
        private: bool = True,
        description: str = "",
        auto_init: bool = False,
    ) -> Optional[Repository]:
        """Create a new repository."""
        pass

    @abstractmethod
    def delete_repo(self, owner: str, name: str) -> bool:
        """Delete a repository."""
        pass

    @abstractmethod
    def repo_exists(self, owner: str, name: str) -> bool:
        """Check if a repository exists."""
        pass

    @abstractmethod
    def setup_push_mirror(
        self, repo: Repository, target_url: str, sync_on_commit: bool = True, interval: str = "8h"
    ) -> bool:
        """Configure push mirror for automatic synchronization."""
        pass

    def verify_credentials(self) -> bool:
        """Verify if the credentials are valid."""
        try:
            response = self.session.get(self._get_api_base_url().replace("/api/v1", "").replace("/api/v4", "/api"))
            return response.status_code in (200, 404)
        except requests.RequestException:
            return False

    def get_user_repos(self, limit: int = 50) -> list:
        """Get list of user repositories."""
        pass
