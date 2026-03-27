"""Telegram integration -- send pipeline notifications via bot."""
from __future__ import annotations

import json
import logging
import os
import urllib.request
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TelegramClient:
    """Lightweight Telegram Bot API client (no SDK dependency)."""

    bot_token: str | None = None
    default_chat_id: str | None = None

    def __post_init__(self) -> None:
        if self.bot_token is None:
            self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if self.default_chat_id is None:
            self.default_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.default_chat_id)

    @property
    def _base_url(self) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(
        self, text: str, chat_id: str | None = None, parse_mode: str = "Markdown"
    ) -> dict | None:
        """Send a message via Telegram Bot API."""
        if not self.enabled:
            logger.debug("Telegram not configured, skipping notification")
            return None

        payload = json.dumps({
            "chat_id": chat_id or self.default_chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }).encode()

        req = urllib.request.Request(
            f"{self._base_url}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                if not result.get("ok"):
                    logger.error("Telegram API error: %s", result.get("description"))
                return result
        except Exception as e:
            logger.error("Telegram notification failed: %s", e)
            return None

    def notify_pipeline_step(
        self, step: str, agent: str, status: str, chat_id: str | None = None
    ) -> None:
        """Send a formatted pipeline step notification."""
        emoji = {"started": "🔄", "completed": "✅", "failed": "❌"}.get(status, "ℹ️")  # noqa: RUF001
        text = f"{emoji} *Pipeline: {step}*\nAgent: `{agent}` | Status: {status}"
        self.send_message(text, chat_id)

    def notify_pipeline_complete(self, request: str, chat_id: str | None = None) -> None:
        """Notify that the full pipeline completed."""
        self.send_message(
            f"🎉 *Pipeline Complete*\nRequest: {request[:200]}",  # noqa: RUF001
            chat_id,
        )
