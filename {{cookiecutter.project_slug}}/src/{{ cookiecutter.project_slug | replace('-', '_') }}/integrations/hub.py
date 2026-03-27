"""Notification hub -- unified interface for all integrations."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .jira import JiraClient
from .linear import LinearClient
from .slack import SlackClient
from .telegram import TelegramClient

logger = logging.getLogger(__name__)


@dataclass
class NotificationHub:
    """Centralized notification dispatcher for pipeline events.

    Initializes all configured integrations and dispatches events
    to each enabled service. Failures in one service don't block others.
    """

    slack: SlackClient = field(default_factory=SlackClient)
    jira: JiraClient = field(default_factory=JiraClient)
    linear: LinearClient = field(default_factory=LinearClient)
    telegram: TelegramClient = field(default_factory=TelegramClient)

    # Track issue keys created for the current pipeline run
    _jira_issue_key: str | None = field(default=None, repr=False)
    _linear_issue_id: str | None = field(default=None, repr=False)

    @property
    def active_services(self) -> list[str]:
        """List of currently enabled integrations."""
        services = []
        if self.slack.enabled:
            services.append("slack")
        if self.jira.enabled:
            services.append("jira")
        if self.linear.enabled:
            services.append("linear")
        if self.telegram.enabled:
            services.append("telegram")
        return services

    def on_pipeline_start(self, request: str) -> None:
        """Called when a new pipeline run begins."""
        logger.info("Notifications active: %s", self.active_services or ["none"])

        # Create tracking issues
        if self.jira.enabled:
            self._jira_issue_key = self.jira.create_issue(
                summary=f"Pipeline: {request[:100]}",
                description=f"Automated pipeline run.\n\nRequest:\n{request}",
            )

        if self.linear.enabled:
            issue = self.linear.create_issue(
                title=f"Pipeline: {request[:100]}",
                description=f"Automated pipeline run.\n\nRequest:\n{request}",
            )
            if issue:
                self._linear_issue_id = issue["id"]

        # Notify messaging channels
        if self.slack.enabled:
            self.slack.post_message(f"🚀 *New Pipeline Started*\n>{request[:300]}")  # noqa: RUF001

        if self.telegram.enabled:
            self.telegram.send_message(f"🚀 *New Pipeline Started*\n{request[:300]}")  # noqa: RUF001

    def on_step_start(self, step: str, agent: str) -> None:
        """Called when a pipeline step begins."""
        if self.slack.enabled:
            self.slack.notify_pipeline_step(step, agent, "started")
        if self.telegram.enabled:
            self.telegram.notify_pipeline_step(step, agent, "started")

    def on_step_complete(self, step: str, agent: str, output: str) -> None:
        """Called when a pipeline step completes successfully."""
        if self.slack.enabled:
            self.slack.notify_pipeline_step(step, agent, "completed")
        if self.telegram.enabled:
            self.telegram.notify_pipeline_step(step, agent, "completed")

        # Add progress comment to tracking issues
        comment = f"Step '{step}' ({agent}) completed.\n\nOutput preview:\n{output[:300]}"
        if self._jira_issue_key:
            self.jira.add_comment(self._jira_issue_key, comment)
        if self._linear_issue_id:
            self.linear.add_comment(self._linear_issue_id, comment)

    def on_step_failed(self, step: str, agent: str, error: str) -> None:
        """Called when a pipeline step fails."""
        if self.slack.enabled:
            self.slack.notify_pipeline_step(step, agent, "failed")
            self.slack.post_message(f"Error: ```{error[:500]}```")
        if self.telegram.enabled:
            self.telegram.notify_pipeline_step(step, agent, "failed")
            self.telegram.send_message(f"Error: `{error[:500]}`")

        comment = f"Step '{step}' ({agent}) FAILED.\n\nError:\n{error[:500]}"
        if self._jira_issue_key:
            self.jira.add_comment(self._jira_issue_key, comment)
        if self._linear_issue_id:
            self.linear.add_comment(self._linear_issue_id, comment)

    def on_pipeline_complete(self, request: str) -> None:
        """Called when the full pipeline completes successfully."""
        if self.slack.enabled:
            self.slack.notify_pipeline_complete(request)
        if self.telegram.enabled:
            self.telegram.notify_pipeline_complete(request)

        # Transition tracking issues to Done
        if self._jira_issue_key:
            self.jira.transition_issue(self._jira_issue_key, "done")
        if self._linear_issue_id:
            self.linear.update_issue_status(self._linear_issue_id, "done")

    def on_pipeline_failed(self, request: str, error: str) -> None:
        """Called when the pipeline fails."""
        msg = f"❌ *Pipeline Failed*\nRequest: {request[:200]}\nError: {error[:300]}"  # noqa: RUF001
        if self.slack.enabled:
            self.slack.post_message(msg)
        if self.telegram.enabled:
            self.telegram.send_message(msg)
