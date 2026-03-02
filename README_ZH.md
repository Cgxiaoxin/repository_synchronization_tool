# 仓库同步工具 (Repository Synchronization Tool)

[English](./README.md) | [中文](./README_ZH.md)

一个用于在多个 Git 托管平台之间同步仓库的 CLI 工具。支持 GitHub、GitLab、Gitee、Gitea 等平台，一次配置，多平台镜像，告别手动推送。

## 功能特性

- **多平台支持**：GitHub、GitLab、Gitee、Gitea、Bitbucket
- **多种同步模式**：
  - 推送镜像（在源平台配置推送镜像）
  - 拉取同步（工具定期拉取并推送）
- **两种触发方式**：
  - Webhook（推送时实时同步）
  - 定时同步（周期性全量同步）
- **CLI 界面**：简单易用的命令行界面
- **配置文件**：基于 YAML 的配置管理

## 安装

```bash
# 从源码安装
pip install -e .

# 或从 PyPI 安装（发布后）
pip install repo-sync
```

## 快速开始

### 1. 初始化配置

```bash
repo-sync init
```

这会创建一个 `config.yaml` 配置文件。请编辑该文件，填入你的平台凭证。

### 2. 配置凭证

你可以在 `config.yaml` 中配置凭证，也可以使用环境变量：

```bash
export GITHUB_TOKEN="your-github-token"
export GITEA_TOKEN="your-gitea-token"
export GITLAB_TOKEN="your-gitlab-token"
```

### 3. 添加同步任务

```bash
# 添加同步任务：从 gitea 同步到 github 和 gitlab
repo-sync add gitea:username/myrepo github:username gitlab:username

# 或使用完整格式
repo-sync add gitea:owner/repo github:owner/repo
```

### 4. 立即同步

```bash
# 同步指定任务
repo-sync sync myrepo

# 或同步所有任务
repo-sync sync --all
```

## 配置示例

`config.yaml` 配置文件示例：

```yaml
version: "1.0"

# 平台凭证
platforms:
  github:
    token: "your-github-token"
  
  gitlab:
    url: "https://gitlab.com"
    token: "your-gitlab-token"
  
  gitea:
    url: "http://gitea.example.com"
    token: "your-gitea-token"

# 同步任务
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

# 定时同步
scheduler:
  enabled: false
  interval: "8h"

# Webhook 服务
webhook:
  enabled: false
  host: "0.0.0.0"
  port: 8080
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `repo-sync init` | 初始化配置文件 |
| `repo-sync add <源> <目标>` | 添加同步任务 |
| `repo-sync remove <名称>` | 移除同步任务 |
| `repo-sync list` | 列出所有同步任务 |
| `repo-sync sync <名称>` | 同步指定任务 |
| `repo-sync sync --all` | 同步所有任务 |
| `repo-sync webhook` | 启动 Webhook 服务 |
| `repo-sync config-show` | 显示当前配置 |

## 使用示例

### 从 Gitea 同步到 GitHub

```bash
# 添加任务
repo-sync add gitea:myuser/myproject github:myuser

# 执行同步
repo-sync sync myproject
```

### 配置自动同步

对于 Gitea 仓库，工具可以自动配置推送镜像：

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

同步时，它会：
1. 如果 GitHub 上不存在则创建仓库
2. 镜像推送所有分支和标签
3. 在 Gitea 上配置推送镜像以实现后续自动同步

### 定时同步

在配置文件中启用调度器：

```yaml
scheduler:
  enabled: true
  interval: "8h"  # 每 8 小时同步一次
```

### Webhook 服务

启动 Webhook 服务以实现实时同步：

```bash
repo-sync webhook --port 8080
```

在 Git 托管平台上配置 Webhook URL：
- **GitHub**：仓库设置 → Webhooks → 添加 webhook
- **GitLab**：项目设置 → Webhooks → 添加 webhook
- **Gitea**：仓库设置 → Git 钩子 → 编辑推送钩子

## 配置说明

### 平台配置

```yaml
platforms:
  github:
    token: "your-github-token"
    # url: "https://api.github.com"  # GitHub Enterprise 时使用
  
  gitlab:
    url: "https://gitlab.com"
    token: "your-gitlab-token"
  
  gitea:
    url: "http://gitea.example.com"
    token: "your-gitea-token"
```

### 同步任务配置

```yaml
sync_tasks:
  - name: "任务名称"
    source:
      platform: "源平台 (gitea/github/gitlab/gitee)"
      owner: "源仓库所有者"
      repo: "源仓库名称"
    targets:
      - platform: "目标平台"
        owner: "目标仓库所有者"
        # repo 可选，默认与源仓库同名
    options:
      # branches: ["main", "develop"]  # 同步指定分支，空则同步所有
      tags: true          # 是否同步标签
      private: true      # 目标仓库是否私有
      auto_init: false   # 目标仓库是否需要初始化
```

### 定时配置

```yaml
scheduler:
  enabled: true
  interval: "8h"  # 支持格式: "30m", "1h", "8h", "1d"
```

### Webhook 配置

```yaml
webhook:
  enabled: true
  host: "0.0.0.0"
  port: 8080
  # secret: "your-webhook-secret"  # Webhook 签名密钥
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行带覆盖率的测试
pytest --cov=repo_sync tests/
```

## 许可证

MIT License
