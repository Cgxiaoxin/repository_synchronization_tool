"""Git operations wrapper for repository synchronization."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional


class GitError(Exception):
    """Exception raised for Git operation errors."""
    pass


class GitOperator:
    """Wrapper for Git operations."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout

    def _run(self, args: List[str], cwd: Optional[str] = None, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a Git command."""
        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                timeout=self.timeout,
                check=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            raise GitError(f"Git command failed: {' '.join(args)}\n{e.stderr}")
        except subprocess.TimeoutExpired as e:
            raise GitError(f"Git command timed out: {' '.join(args)}")
        except FileNotFoundError:
            raise GitError("Git is not installed or not in PATH")

    def version(self) -> str:
        """Get Git version."""
        result = self._run(["git", "--version"])
        return result.stdout.strip()

    def clone_mirror(self, source_url: str, target_dir: str, username: Optional[str] = None, password: Optional[str] = None) -> None:
        """Clone a repository using mirror mode."""
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        clone_url = self._add_auth(source_url, username, password)
        self._run(["git", "clone", "--mirror", clone_url, target_dir])

    def push_mirror(self, repo_dir: str, target_url: str, username: Optional[str] = None, password: Optional[str] = None) -> None:
        """Push all refs to target repository using mirror mode."""
        push_url = self._add_auth(target_url, username, password)
        
        remote_name = "target"
        self._run(["git", "-C", repo_dir, "remote", "add", remote_name, push_url], capture_output=False)
        self._run(["git", "-C", repo_dir, "push", remote_name, "--mirror"], capture_output=False)

    def add_remote(self, repo_dir: str, name: str, url: str, username: Optional[str] = None, password: Optional[str] = None) -> None:
        """Add a remote to a repository."""
        remote_url = self._add_auth(url, username, password)
        
        result = self._run(["git", "-C", repo_dir, "remote", "-v"])
        existing_remotes = result.stdout
        
        if name in existing_remotes:
            self._run(["git", "-C", repo_dir, "remote", "set-url", name, remote_url], capture_output=False)
        else:
            self._run(["git", "-C", repo_dir, "remote", "add", name, remote_url], capture_output=False)

    def push_to_remote(self, repo_dir: str, remote_name: str, refspec: str = "refs/heads/*:refs/heads/*") -> None:
        """Push refs to a remote."""
        self._run(["git", "-C", repo_dir, "push", remote_name, refspec], capture_output=False)

    def fetch_all(self, repo_dir: str) -> None:
        """Fetch all refs from all remotes."""
        self._run(["git", "-C", repo_dir, "fetch", "--all", "--tags"], capture_output=False)

    def get_branches(self, repo_dir: str) -> List[str]:
        """Get list of local branches."""
        result = self._run(["git", "-C", repo_dir, "branch", "--format=%(refname:short)"])
        branches = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]
        return branches

    def get_remote_branches(self, repo_dir: str, remote: str = "origin") -> List[str]:
        """Get list of remote branches."""
        result = self._run(["git", "-C", repo_dir, "branch", "-r", "--format=%(refname:short)"])
        branches = [b.strip() for b in result.stdout.strip().split("\n") if b.strip() and b.startswith(remote + "/")]
        return branches

    def get_tags(self, repo_dir: str) -> List[str]:
        """Get list of tags."""
        result = self._run(["git", "-C", repo_dir, "tag", "--list"])
        tags = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
        return tags

    def get_latest_commit(self, repo_dir: str, branch: str = "main") -> Optional[str]:
        """Get the latest commit hash for a branch."""
        try:
            result = self._run(["git", "-C", repo_dir, "log", "-1", "--format=%H", branch])
            return result.stdout.strip()
        except GitError:
            try:
                result = self._run(["git", "-C", repo_dir, "log", "-1", "--format=%H", "master"])
                return result.stdout.strip()
            except GitError:
                return None

    def init_bare(self, repo_dir: str) -> None:
        """Initialize a bare repository."""
        os.makedirs(repo_dir, exist_ok=True)
        self._run(["git", "init", "--bare", repo_dir])

    def cleanup(self, repo_dir: str) -> None:
        """Clean up a temporary repository directory."""
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    @staticmethod
    def _add_auth(url: str, username: Optional[str], password: Optional[str]) -> str:
        """Add authentication to a URL if provided."""
        if not username and not password:
            return url

        if url.startswith("http://"):
            auth_url = url.replace("http://", f"http://{username}:{password}@", 1)
        elif url.startswith("https://"):
            auth_url = url.replace("https://", f"https://{username}:{password}@", 1)
        else:
            auth_url = url

        return auth_url

    @staticmethod
    def get_temp_dir(prefix: str = "repo_sync_") -> str:
        """Get a temporary directory for repository operations."""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        return temp_dir
