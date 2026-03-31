"""Slack watcher — polls channel for new messages, agents respond in threads."""
from __future__ import annotations

import logging
import signal
import time
from dataclasses import dataclass, field

from ..agent import Agent
from ..config import Config
from ..orchestrator import Pipeline

logger = logging.getLogger(__name__)

CMD_ANALYZE = "analyze"
CMD_STATUS = "status"
CMD_HELP = "help"


@dataclass
class SlackWatcher:
    """Polls Slack channel for new messages and triggers agent responses."""

    config: Config = field(default_factory=Config)
    poll_interval: int = 5
    _last_ts: str | None = None
    _bot_user_id: str | None = None
    _running: bool = True

    def run(self) -> None:
        """Start polling loop."""
        def _handle_signal(signum: int, _frame: object) -> None:
            logger.info("Received signal %s, stopping watcher", signum)
            self._running = False

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

        from ..integrations.slack import SlackClient

        slack = SlackClient(
            bot_token=self.config.slack_bot_token,
            default_channel=self.config.slack_channel_id,
        )

        self._bot_user_id = slack.get_bot_user_id()
        logger.info("Slack bot user ID: %s", self._bot_user_id)

        # Start from now (don't process old messages)
        self._last_ts = str(time.time())

        logger.info(
            "Slack watcher started — polling channel %s every %ds",
            self.config.slack_channel_id, self.poll_interval,
        )

        while self._running:
            try:
                messages = slack.get_messages(oldest=self._last_ts, limit=10)

                for msg in messages:
                    if msg.get("bot_id") or msg.get("user") == self._bot_user_id:
                        continue

                    text = msg.get("text", "").strip()
                    if not text:
                        continue

                    ts = msg.get("ts", "")
                    self._last_ts = ts
                    user = msg.get("user", "unknown")

                    logger.info("New Slack message from %s: %s", user, text[:100])
                    self._handle_message(slack, text, ts)

            except Exception:
                logger.exception("Slack poll failed")

            for _ in range(self.poll_interval):
                if not self._running:
                    break
                time.sleep(1)

        logger.info("Slack watcher stopped")

    def _parse_command(self, text: str) -> tuple[str, str]:
        """Parse command from message text."""
        text = text.strip()
        if self._bot_user_id:
            text = text.replace(f"<@{self._bot_user_id}>", "").strip()

        lower = text.lower()
        if lower.startswith(CMD_ANALYZE):
            return CMD_ANALYZE, text[len(CMD_ANALYZE):].strip()
        if lower.startswith(CMD_STATUS):
            return CMD_STATUS, ""
        if lower.startswith(CMD_HELP):
            return CMD_HELP, ""

        return "chat", text

    def _handle_message(self, slack: "SlackClient", text: str, thread_ts: str) -> None:
        """Handle a single message."""
        from ..integrations.slack import SlackClient

        command, argument = self._parse_command(text)

        if command == CMD_HELP:
            slack.post_message(
                "*Available commands:*\n"
                "- `analyze <request>` — run full agent pipeline\n"
                "- `status` — show active pipelines\n"
                "- `help` — show this message\n"
                "- Or just write a message — BA agent will respond",
                thread_ts=thread_ts,
            )
            return

        if command == CMD_STATUS:
            slack.post_message(
                ":information_source: No active pipelines (stateless mode)",
                thread_ts=thread_ts,
            )
            return

        if command == CMD_ANALYZE:
            if not argument:
                slack.post_message(
                    ":warning: Usage: `analyze <request description>`",
                    thread_ts=thread_ts,
                )
                return
            pipeline = Pipeline(config=self.config)
            pipeline.notifications.slack_thread_ts = thread_ts
            try:
                pipeline.run(argument)
            except Exception as e:
                slack.post_message(f":x: Pipeline failed: {e}", thread_ts=thread_ts)
            return

        # Default: BA agent responds to the message in thread
        try:
            agent = Agent(role="business-analyst", config=self.config)
            response = agent.run(
                f"A team member asked in Slack:\n\n{text}\n\n"
                f"Provide a helpful, concise response."
            )
            slack.post_message(response[:4000], thread_ts=thread_ts)
        except Exception as e:
            logger.exception("Agent response failed")
            slack.post_message(f":warning: Could not generate response: {e}", thread_ts=thread_ts)
