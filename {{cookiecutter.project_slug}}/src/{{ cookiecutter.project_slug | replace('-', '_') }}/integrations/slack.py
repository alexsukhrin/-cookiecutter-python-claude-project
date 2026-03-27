"""Slack integration -- post pipeline notifications to channels."""
from __future__ import annotations

import json
import logging
import os
import urllib.request
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SlackClient:
    """Lightweight Slack client using Bot Token + Web API (no SDK dependency)."""

    bot_token: str | None = None
    default_channel: str = "#general"

    def __post_init__(self) -> None:
        if self.bot_token is None:
            self.bot_token = os.getenv("SLACK_BOT_TOKEN")

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token)

    def post_message(self, text: str, channel: str | None = None) -> dict | None:
        """Post a message to a Slack channel."""
        if not self.enabled:
            logger.debug("Slack not configured, skipping notification")
            return None

        channel = channel or self.default_channel
        payload = json.dumps({"channel": channel, "text": text}).encode()

        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                if not result.get("ok"):
                    logger.error("Slack API error: %s", result.get("error"))
                return result
        except Exception as e:
            logger.error("Slack notification failed: %s", e)
            return None

    def notify_pipeline_step(
        self, step: str, agent: str, status: str, channel: str | None = None
    ) -> None:
        """Send a formatted pipeline step notification."""
        emoji = {"started": "🔄", "completed": "✅", "failed": "❌"}.get(status, "ℹ️")  # noqa: RUF001
        text = f"{emoji} *Pipeline Step: {step}*\nAgent: `{agent}` | Status: {status}"
        self.post_message(text, channel)

    def notify_pipeline_complete(self, request: str, channel: str | None = None) -> None:
        """Notify that the full pipeline completed."""
        self.post_message(
            f"🎉 *Pipeline Complete*\nRequest: {request[:200]}",  # noqa: RUF001
            channel,
        )
