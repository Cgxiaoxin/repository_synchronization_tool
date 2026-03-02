"""GitLab platform adapter."""

from typing import Optional

import requests

from .base import BasePlatform
from ..models import Platform, Repository


class GitLabPlatform(BasePlatform):
    """GitLab platform adapter."""

    def _get_headers(self) -> dict:
        return {
            "PRIVATE-TOKEN": self.config.token,
        }

    def _get_api_base_url(self) -> str:
        base = self.config.base_url
        if "/api" not in base:
            return f"{base}/api/v4"
        return base

    def _get_clone_url(self, owner: str, name: str) -> str:
        return f"{self.config.base_url}/{owner}/{name}.git"

    def get_user_repos(self, limit: int = 50) -> list:
        url = f"{self._get_api_base_url()}/projects"
        params = {"per_page": min(limit, 100), "membership": True}
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
        url = f"{self._get_api_base_url()}/projects"
        data = {
            "name": name,
            "description": description,
            "visibility": "private" if private else "public",
            "initialize_with_readme": auto_init,
        }
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 201:
                repo_data = response.json()
                return Repository(
                    platform=Platform.GITLAB,
                    owner=repo_data.get("namespace", {}).get("full_path", "").lstrip("/"),
                    name=repo_data.get("name", name),
                    clone_url=repo_data.get("http_url_to_repo", ""),
                    is_private=repo_data.get("visibility") == "private",
                    description=repo_data.get("description", description),
                )
            elif response.status_code == 400:
                project_id = f"{self._get_current_user()}/{name}"
                return self.get_repo(self._get_current_user(), name)
        except requests.RequestException:
            pass
        return None

    def delete_repo(self, owner: str, name: str) -> bool:
        project_id = f"{owner}/{name}"
        url = f"{self._get_api_base_url()}/projects/{project_id.replace('/', '%2F')}"
        try:
            response = self.session.delete(url)
            return response.status_code == 204
        except requests.RequestException:
            return False

    def repo_exists(self, owner: str, name: str) -> bool:
        project_id = f"{owner}/{name}"
        url = f"{self._get_api_base_url()}/projects/{project_id.replace('/', '%2F')}"
        try:
            response = self.session.get(url)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def setup_push_mirror(
        self, repo: Repository, target_url: str, sync_on_commit: bool = True, interval: str = "8h"
    ) -> bool:
        project_id = f"{repo.owner}/{repo.name}"
        url = f"{self._get_api_base_url()}/projects/{project_id.replace('/', '%2F')}"
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                return False
            
            mirror_data = {
                "mirror": True,
                "mirror_trigger_builds": sync_on_commit,
            }
            patch_url = f"{url}"
            response = self.session.put(patch_url, json=mirror_data)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _get_current_user(self) -> str:
        url = f"{self._get_api_base_url()}/user"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json().get("username", "")
        except requests.RequestException:
            pass
        return ""
