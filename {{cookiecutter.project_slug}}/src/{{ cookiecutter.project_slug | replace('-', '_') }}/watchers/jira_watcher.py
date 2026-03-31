"""Jira watcher — polls for new tickets and triggers pipeline."""
from __future__ import annotations

import logging
import signal
import time
from dataclasses import dataclass, field

from ..config import Config
from ..orchestrator import Pipeline

logger = logging.getLogger(__name__)


@dataclass
class JiraWatcher:
    """Polls Jira for new assigned tickets and runs pipeline for each."""

    config: Config = field(default_factory=Config)
    poll_interval: int = 5
    _seen: set[str] = field(default_factory=set)
    _running: bool = True

    def run(self) -> None:
        """Start polling loop."""
        def _handle_signal(signum: int, _frame: object) -> None:
            logger.info("Received signal %s, stopping watcher", signum)
            self._running = False

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

        from ..integrations.jira import JiraClient

        jira = JiraClient(
            base_url=self.config.jira_base_url,
            email=self.config.jira_email,
            api_token=self.config.jira_api_token,
            project_key=self.config.jira_project_key,
        )

        logger.info(
            "Jira watcher started — polling every %ds (project: %s)",
            self.poll_interval, self.config.jira_project_key,
        )

        while self._running:
            try:
                issues = jira.fetch_assigned_issues(
                    assignee=self.config.jira_assignee or None,
                    status="To Do",
                )
                new_issues = [i for i in issues if i["key"] not in self._seen]

                for issue in new_issues:
                    self._seen.add(issue["key"])
                    logger.info("New Jira ticket: %s — %s", issue["key"], issue["summary"])

                    try:
                        pipeline = Pipeline(config=self.config)
                        pipeline.run_from_jira(issue["key"])
                    except Exception:
                        logger.exception("Pipeline failed for %s", issue["key"])

            except Exception:
                logger.exception("Jira poll failed")

            for _ in range(self.poll_interval):
                if not self._running:
                    break
                time.sleep(1)

        logger.info("Jira watcher stopped")
