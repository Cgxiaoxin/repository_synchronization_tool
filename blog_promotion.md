# 我写了一个开源工具，解决多平台仓库同步的痛点

作为一名经常使用多个 Git 托管平台的开发者，我经常面临这样一个问题：项目需要同时同步到多个平台，比如公司内部用 Gitea，对外开源需要同步到 GitHub，有时候还需要备份到 GitLab。

手动同步不仅繁琐，还容易遗漏。直到我实在受不了了，决定自己动手写一个工具。

## 痛点回顾

- 每次代码提交后，需要手动推送到多个平台
- 不同平台之间的仓库维护麻烦
- 团队协作时，成员可能使用不同的平台
- 想要做一个开源项目，需要同时同步到多个代码托管平台

## 我的解决方案：repo-sync

今天给大家介绍我开源的仓库同步工具 **repo-sync**，一个简洁的 CLI 工具，专门解决多平台仓库同步的问题。

### 核心功能

**1. 多平台支持**
支持主流的 Git 托管平台：GitHub、GitLab、Gitee、Gitea、Bitbucket，几乎覆盖了大多数开发者的使用场景。

**2. 多种同步模式**
- 推送镜像模式：在源平台配置推送镜像，后续提交自动同步
- 拉取同步模式：工具定期从源平台拉取并推送到目标平台

**3. 两种触发方式**
- Webhook 实时触发：代码提交后立即同步
- 定时全量同步：按照配置的间隔定期同步

### 快速上手

安装非常简单：

```bash
pip install repo-sync
```

初始化配置：

```bash
repo-sync init
```

添加同步任务（以 Gitea 同步到 GitHub 为例）：

```bash
repo-sync add gitea:myuser/myproject github:myuser
```

执行同步：

```bash
repo-sync sync myproject
```

配置文件示例：

```yaml
platforms:
  github:
    token: "your-github-token"
  gitea:
    url: "http://gitea.example.com"
    token: "your-gitea-token"

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

### 适用场景

1. **开源项目多平台同步**：代码主体在 GitHub，同时同步到 Gitee 供国内开发者
2. **企业内外部署**：内部使用 Gitea，需要同步到公网 GitHub
3. **跨平台备份**：将仓库同时备份到多个平台
4. **团队协作**：不同团队成员使用不同平台，通过工具统一同步

### 技术细节

- 使用 Python 3.8+ 开发
- 基于 Click 构建 CLI
- 使用 Git mirror 模式保证分支和标签完整同步
- 支持通过环境变量管理凭证，安全性有保障

## 开源地址

项目已经开源在 GitHub：[repository_synchronization_tool](https://github.com/Cgxiaoxin/repository_synchronization_tool)

欢迎 star、fork 和贡献！

---

如果你也有类似的痛点，不妨试试这个工具。有什么问题，欢迎在评论区交流。