"""GitHub platform adapter."""

from typing import Optional

import requests

from .base import BasePlatform
from ..models import Platform, Repository


class GitHubPlatform(BasePlatform):
    """GitHub platform adapter."""

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"token {self.config.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get_api_base_url(self) -> str:
        base = self.config.base_url
        if "api.github.com" in base:
            return base
        elif "github.com" in base:
            return "https://api.github.com"
        else:
            return f"{base}/api/v3"

    def _get_clone_url(self, owner: str, name: str) -> str:
        return f"{self.config.base_url}/{owner}/{name}.git"

    def get_user_repos(self, limit: int = 50) -> list:
        url = f"{self._get_api_base_url()}/user/repos"
        params = {"per_page": min(limit, 100)}
        repos = []
        page = 1
        while len(repos) < limit:
            params["page"] = page
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        return repos[:limit]

    def create_repo(
        self,
        name: str,
        private: bool = True,
        description: str = "",
        auto_init: bool = False,
    ) -> Optional[Repository]:
        url = f"{self._get_api_base_url()}/user/repos"
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
        }
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 201:
                repo_data = response.json()
                return Repository(
                    platform=Platform.GITHUB,
                    owner=repo_data.get("owner", {}).get("login", ""),
                    name=repo_data.get("name", name),
                    clone_url=repo_data.get("clone_url", ""),
                    is_private=repo_data.get("private", private),
                    description=repo_data.get("description", description),
                )
            elif response.status_code == 422:
                return self.get_repo(self._get_current_user(), name)
        except requests.RequestException:
            pass
        return None

    def delete_repo(self, owner: str, name: str) -> bool:
        url = f"{self._get_api_base_url()}/repos/{owner}/{name}"
        try:
            response = self.session.delete(url)
            return response.status_code == 204
        except requests.RequestException:
            return False

    def repo_exists(self, owner: str, name: str) -> bool:
        url = f"{self._get_api_base_url()}/repos/{owner}/{name}"
        try:
            response = self.session.get(url)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def setup_push_mirror(
        self, repo: Repository, target_url: str, sync_on_commit: bool = True, interval: str = "8h"
    ) -> bool:
        return True

    def _get_current_user(self) -> str:
        url = f"{self._get_api_base_url()}/user"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json().get("login", "")
        except requests.RequestException:
            pass
        return ""
