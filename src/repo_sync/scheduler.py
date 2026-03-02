"""Scheduler for periodic synchronization."""

import logging
import threading
import time
from typing import Optional

from .config import ConfigManager
from .sync_engine import SyncEngine, SyncResult

logger = logging.getLogger(__name__)


class Scheduler:
    """Scheduler for periodic synchronization tasks."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load()
        self.engine = SyncEngine(config_path)
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        """Start the scheduler."""
        if not self.config.scheduler.enabled:
            logger.info("Scheduler is disabled in configuration")
            return

        self.running = True
        interval = self.config.scheduler.get_interval_seconds()
        logger.info(f"Starting scheduler with interval: {interval} seconds")

        self.thread = threading.Thread(target=self._run_loop, args=(interval,), daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def _run_loop(self, interval: int):
        """Main scheduler loop."""
        while self.running:
            try:
                logger.info("Running scheduled synchronization...")
                results = self.engine.sync_all()
                success_count = sum(1 for r in results if r.success)
                logger.info(f"Scheduled sync completed: {success_count}/{len(results)} succeeded")
            except Exception as e:
                logger.error(f"Scheduled synchronization failed: {e}")

            time.sleep(interval)


def start_scheduler(config_path: Optional[str] = None):
    """Start the scheduler (convenience function)."""
    scheduler = Scheduler(config_path)
    scheduler.start()
    return scheduler
