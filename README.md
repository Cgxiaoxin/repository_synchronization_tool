# Repository Synchronization Tool

[English](./README.md) | [中文](./README_ZH.md)

A CLI tool for synchronizing repositories across multiple Git hosting platforms. Supports GitHub, GitLab, Gitee, Gitea, and more. One configuration, multi-platform mirror.

## Features

- **Multi-platform support**: GitHub, GitLab, Gitee, Gitea, Bitbucket
- **Multiple sync modes**: 
  - Push mirror (configure push mirror on source platform)
  - Pull sync (tool pulls and pushes)
- **Two triggering methods**:
  - Webhook (real-time sync on push)
  - Scheduled sync (periodic full sync)
- **CLI interface**: Easy to use command-line interface
- **Configuration file**: YAML-based configuration

## Installation

```bash
# From source
pip install -e .

# Or install from PyPI (when published)
pip install repo-sync
```

## Quick Start

### 1. Initialize configuration

```bash
repo-sync init
```

This creates a `config.yaml` file. Edit it with your platform credentials.

### 2. Configure credentials

You can configure credentials in `config.yaml` or use environment variables:

```bash
export GITHUB_TOKEN="your-github-token"
export GITEA_TOKEN="your-gitea-token"
export GITLAB_TOKEN="your-gitlab-token"
```

### 3. Add sync task

```bash
# Add a sync task: from gitea to github and gitlab
repo-sync add gitea:username/myrepo github:username gitlab:username

# Or use full format
repo-sync add gitea:owner/repo github:owner/repo
```

### 4. Sync now

```bash
# Sync a specific task
repo-sync sync myrepo

# Or sync all tasks
repo-sync sync --all
```

## Configuration

Example `config.yaml`:

```yaml
version: "1.0"

platforms:
  github:
    token: "your-github-token"
  gitlab:
    url: "https://gitlab.com"
    token: "your-gitlab-token"
  gitea:
    url: "http://gitea.example.com"
    token: "your-gitea-token"

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
      tags: true
      private: true
      auto_init: false

scheduler:
  enabled: false
  interval: "8h"

webhook:
  enabled: false
  host: "0.0.0.0"
  port: 8080
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `repo-sync init` | Initialize configuration file |
| `repo-sync add <source> <targets>` | Add a sync task |
| `repo-sync remove <name>` | Remove a sync task |
| `repo-sync list` | List all sync tasks |
| `repo-sync sync <name>` | Sync a specific task |
| `repo-sync sync --all` | Sync all tasks |
| `repo-sync webhook` | Start webhook server |
| `repo-sync config-show` | Show current configuration |

## Usage Examples

### Sync from Gitea to GitHub

```bash
# Add task
repo-sync add gitea:myuser/myproject github:myuser

# Sync
repo-sync sync myproject
```

### Configure auto-sync

For Gitea repositories, the tool can configure push mirrors automatically:

```yaml
sync_tasks:
  - name: "my-project"
    source:
      platform: "gitea"
      owner: "myuser"
      repo: "my-project"
    targets:
      - platform: "github"
        owner: "myuser"
```

When syncing, it will:
1. Create repository on GitHub if not exists
2. Mirror push all branches and tags
3. Configure push mirror on Gitea for automatic future syncs

### Scheduled sync

Enable scheduler in config:

```yaml
scheduler:
  enabled: true
  interval: "8h"  # Sync every 8 hours
```

### Webhook server

Start webhook server for real-time sync:

```bash
repo-sync webhook --port 8080
```

Configure webhook URL in your Git hosting platform:
- GitHub: Repository Settings → Webhooks → Add webhook
- GitLab: Project Settings → Webhooks → Add webhook
- Gitea: Repository Settings → Git Hooks → Edit push hook

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=repo_sync tests/
```

## License

MIT License
