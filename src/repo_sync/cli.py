"""Command-line interface for repository synchronization tool."""

import logging
import sys
from pathlib import Path

import click

from .__version__ import __version__
from .config import ConfigManager, get_default_config_template
from .models import Platform, Repository, SyncOptions, SyncTask
from .sync_engine import SyncEngine, SyncResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
def cli():
    """Repository Synchronization Tool - Sync your repos across platforms."""
    pass


@cli.command()
@click.option("--config", "-c", "config_path", help="Path to configuration file")
@click.option("--force", is_flag=True, help="Force overwrite existing config")
def init(config_path, force):
    """Initialize a new configuration file."""
    config_file = config_path or "config.yaml"
    
    if Path(config_file).exists() and not force:
        click.echo(f"Configuration file '{config_file}' already exists. Use --force to overwrite.")
        return

    template = get_default_config_template()
    Path(config_file).write_text(template, encoding="utf-8")
    click.echo(f"Configuration file '{config_file}' created successfully.")
    click.echo("Please edit it and add your platform credentials.")


@cli.command()
@click.argument("source", required=False)
@click.argument("targets", nargs=-1, required=False)
@click.option("--name", help="Task name (defaults to repo name)")
@click.option("--private/--public", "private", default=True, help="Target repository visibility")
@click.option("--config", "-c", "config_path", help="Path to configuration file")
def add(source, targets, name, private, config_path):
    """Add a new synchronization task.
    
    Examples:
        repo-sync add gitea/user/repo github:user gitlab:user
        repo-sync add github:owner/repo gitee:owner --name my-sync
    """
    if not source:
        click.echo("Error: SOURCE is required. Format: platform:owner/repo")
        return

    if not targets:
        click.echo("Error: At least one TARGET is required. Format: platform:owner")
        return

    try:
        source_platform, source_owner, source_repo = _parse_repo_spec(source)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    target_repos = []
    for target_spec in targets:
        try:
            target_platform, target_owner, target_repo = _parse_repo_spec(target_spec)
            target_repos.append(Repository(
                platform=target_platform,
                owner=target_owner,
                name=target_repo or source_repo,
            ))
        except ValueError as e:
            click.echo(f"Error parsing target '{target_spec}': {e}")
            return

    source_repo_obj = Repository(
        platform=source_platform,
        owner=source_owner,
        name=source_repo,
    )

    options = SyncOptions(private=private)
    task_name = name or source_repo

    task = SyncTask(
        name=task_name,
        source=source_repo_obj,
        targets=target_repos,
        options=options,
    )

    engine = SyncEngine(config_path)
    if engine.add_task(task):
        click.echo(f"Task '{task_name}' added successfully.")
    else:
        click.echo("Failed to add task.")
        sys.exit(1)


@cli.command()
@click.argument("task_name")
@click.option("--config", "-c", "config_path", help="Path to configuration file")
def remove(task_name, config_path):
    """Remove a synchronization task."""
    engine = SyncEngine(config_path)
    if engine.remove_task(task_name):
        click.echo(f"Task '{task_name}' removed successfully.")
    else:
        click.echo(f"Task '{task_name}' not found.")
        sys.exit(1)


@cli.command("list")
@click.option("--config", "-c", "config_path", help="Path to configuration file")
def list_tasks(config_path):
    """List all synchronization tasks."""
    engine = SyncEngine(config_path)
    tasks = engine.list_tasks()

    if not tasks:
        click.echo("No synchronization tasks configured.")
        click.echo("Run 'repo-sync add' to add a new task.")
        return

    click.echo(f"\nConfigured tasks: {len(tasks)}\n")
    for task in tasks:
        targets_str = ", ".join([t.full_name for t in task.targets])
        click.echo(f"  {task.name}")
        click.echo(f"    Source: {task.source.platform.value}/{task.source.full_name}")
        click.echo(f"    Targets: {targets_str}")
        click.echo()


@cli.command()
@click.argument("task_name", required=False)
@click.option("--all", "sync_all", is_flag=True, help="Sync all tasks")
@click.option("--config", "-c", "config_path", help="Path to configuration file")
def sync(task_name, sync_all, config_path):
    """Synchronize repositories.
    
    Examples:
        repo-sync sync my-task
        repo-sync sync --all
    """
    engine = SyncEngine(config_path)

    if sync_all:
        click.echo("Syncing all tasks...\n")
        results = engine.sync_all()
    elif task_name:
        click.echo(f"Syncing task '{task_name}'...\n")
        results = engine.sync_by_name(task_name)
    else:
        click.echo("Error: Specify a task name or use --all")
        return

    _print_results(results)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Webhook server host")
@click.option("--port", default=8080, type=int, help="Webhook server port")
@click.option("--config", "-c", "config_path", help="Path to configuration file")
def webhook(host, port, config_path):
    """Start webhook server for real-time synchronization."""
    click.echo(f"Starting webhook server on {host}:{port}")
    click.echo("Press Ctrl+C to stop.")
    
    try:
        from .webhook import run_webhook_server
        run_webhook_server(host, port, config_path)
    except ImportError:
        click.echo("Error: Flask is required for webhook server.")
        click.echo("Install with: pip install repo-sync[webhook]")
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", "config_path", help="Path to configuration file")
def config_show(config_path):
    """Show current configuration."""
    manager = ConfigManager(config_path)
    config = manager.load()
    
    click.echo("Current configuration:")
    click.echo(f"  Platforms: {', '.join(config.platforms.keys())}")
    click.echo(f"  Tasks: {len(config.sync_tasks)}")
    click.echo(f"  Scheduler: {'enabled' if config.scheduler.enabled else 'disabled'}")
    click.echo(f"  Webhook: {'enabled' if config.webhook.enabled else 'disabled'}")


def _parse_repo_spec(spec: str) -> tuple:
    """Parse repository specification.
    
    Formats:
        platform:owner/repo
        platform:owner (repo defaults to same as owner)
    """
    if ":" not in spec:
        raise ValueError("Invalid format. Use: platform:owner/repo")

    parts = spec.split(":", 1)
    platform_str = parts[0].lower()
    rest = parts[1]

    try:
        platform = Platform(platform_str)
    except ValueError:
        raise ValueError(f"Unknown platform: {platform_str}")

    if "/" not in rest:
        raise ValueError("Invalid format. Use: platform:owner/repo")

    path_parts = rest.split("/", 1)
    owner = path_parts[0]
    repo = path_parts[1] if len(path_parts) > 1 else ""

    return platform, owner, repo


def _print_results(results: list):
    """Print synchronization results."""
    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count

    for result in results:
        status = click.style("✓", fg="green") if result.success else click.style("✗", fg="red")
        click.echo(f"  {status} {result.message}")

    click.echo(f"\nSummary: {success_count} succeeded, {fail_count} failed")

    if fail_count > 0:
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
