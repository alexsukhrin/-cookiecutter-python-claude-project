"""Tests for integration clients and notification hub."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from {{ cookiecutter.project_slug | replace('-', '_') }}.integrations.hub import NotificationHub
from {{ cookiecutter.project_slug | replace('-', '_') }}.integrations.jira import JiraClient
from {{ cookiecutter.project_slug | replace('-', '_') }}.integrations.linear import LinearClient
from {{ cookiecutter.project_slug | replace('-', '_') }}.integrations.slack import SlackClient
from {{ cookiecutter.project_slug | replace('-', '_') }}.integrations.telegram import TelegramClient


class TestSlackClient:
    def test_disabled_without_token(self):
        client = SlackClient(bot_token=None)
        assert not client.enabled

    def test_enabled_with_token(self):
        client = SlackClient(bot_token="xoxb-test")
        assert client.enabled

    def test_post_message_skips_when_disabled(self):
        client = SlackClient(bot_token=None)
        assert client.post_message("test") is None

    @patch("urllib.request.urlopen")
    def test_post_message_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"ok": true}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = SlackClient(bot_token="xoxb-test")
        result = client.post_message("hello", "#test")
        assert result["ok"] is True


class TestJiraClient:
    def test_disabled_without_credentials(self):
        client = JiraClient(base_url=None)
        assert not client.enabled

    def test_enabled_with_credentials(self):
        client = JiraClient(
            base_url="https://test.atlassian.net",
            api_token="token",
            user_email="user@test.com",
        )
        assert client.enabled


class TestLinearClient:
    def test_disabled_without_key(self):
        client = LinearClient(api_key=None)
        assert not client.enabled

    def test_enabled_with_key(self):
        client = LinearClient(api_key="lin_api_test")
        assert client.enabled


class TestTelegramClient:
    def test_disabled_without_config(self):
        client = TelegramClient(bot_token=None, default_chat_id=None)
        assert not client.enabled

    def test_enabled_with_config(self):
        client = TelegramClient(bot_token="123:ABC", default_chat_id="456")
        assert client.enabled

    def test_send_message_skips_when_disabled(self):
        client = TelegramClient(bot_token=None, default_chat_id=None)
        assert client.send_message("test") is None


class TestNotificationHub:
    def test_no_active_services_by_default(self):
        hub = NotificationHub(
            slack=SlackClient(bot_token=None),
            jira=JiraClient(base_url=None),
            linear=LinearClient(api_key=None),
            telegram=TelegramClient(bot_token=None, default_chat_id=None),
        )
        assert hub.active_services == []

    def test_active_services_detected(self):
        hub = NotificationHub(
            slack=SlackClient(bot_token="xoxb-test"),
            jira=JiraClient(base_url=None),
            linear=LinearClient(api_key="lin_test"),
            telegram=TelegramClient(bot_token=None, default_chat_id=None),
        )
        assert "slack" in hub.active_services
        assert "linear" in hub.active_services
        assert "jira" not in hub.active_services

    def test_on_pipeline_start_no_crash_without_services(self):
        hub = NotificationHub(
            slack=SlackClient(bot_token=None),
            jira=JiraClient(base_url=None),
            linear=LinearClient(api_key=None),
            telegram=TelegramClient(bot_token=None, default_chat_id=None),
        )
        # Should not raise even with no services configured
        hub.on_pipeline_start("test request")
        hub.on_step_start("step1", "developer")
        hub.on_step_complete("step1", "developer", "output")
        hub.on_pipeline_complete("test request")
