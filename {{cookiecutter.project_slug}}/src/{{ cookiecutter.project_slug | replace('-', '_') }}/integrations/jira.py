"""Jira integration -- create and update issues for pipeline tasks."""
from __future__ import annotations

import base64
import json
import logging
import os
import urllib.request
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

STATUS_MAP = {
    "draft": "To Do",
    "in_review": "In Review",
    "approved": "To Do",
    "in_progress": "In Progress",
    "done": "Done",
}


@dataclass
class JiraClient:
    """Lightweight Jira Cloud client using REST API v3 (no SDK dependency)."""

    base_url: str | None = None
    api_token: str | None = None
    user_email: str | None = None
    project_key: str = "{{ cookiecutter.jira_project_key }}"
    _headers: dict = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url or os.getenv("JIRA_URL", "").rstrip("/")
        self.api_token = self.api_token or os.getenv("JIRA_API_TOKEN")
        self.user_email = self.user_email or os.getenv("JIRA_USER_EMAIL")
        if self.base_url and self.api_token and self.user_email:
            creds = base64.b64encode(
                f"{self.user_email}:{self.api_token}".encode()
            ).decode()
            self._headers = {
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.api_token and self.user_email)

    def _request(self, method: str, path: str, data: dict | None = None) -> dict | None:
        """Make an authenticated request to Jira REST API."""
        if not self.enabled:
            logger.debug("Jira not configured, skipping")
            return None

        url = f"{self.base_url}/rest/api/3/{path.lstrip('/')}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read()) if resp.status != 204 else {}
        except Exception as e:
            logger.error("Jira API error (%s %s): %s", method, path, e)
            return None

    def create_issue(
        self,
        summary: str,
        description: str = "",
        issue_type: str = "Task",
        priority: str = "Medium",
    ) -> str | None:
        """Create a Jira issue. Returns the issue key (e.g. PROJ-123)."""
        result = self._request(
            "POST",
            "issue",
            {
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": description}],
                            }
                        ],
                    },
                    "issuetype": {"name": issue_type},
                    "priority": {"name": priority},
                }
            },
        )
        if result and "key" in result:
            logger.info("Created Jira issue: %s", result["key"])
            return result["key"]
        return None

    def add_comment(self, issue_key: str, body: str) -> dict | None:
        """Add a comment to a Jira issue."""
        return self._request(
            "POST",
            f"issue/{issue_key}/comment",
            {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": body}],
                        }
                    ],
                }
            },
        )

    def transition_issue(self, issue_key: str, status: str) -> bool:
        """Transition a Jira issue to a new status."""
        target = STATUS_MAP.get(status, status)
        # Get available transitions
        result = self._request("GET", f"issue/{issue_key}/transitions")
        if not result:
            return False

        transition_id = None
        for t in result.get("transitions", []):
            if t["name"].lower() == target.lower():
                transition_id = t["id"]
                break

        if transition_id:
            self._request(
                "POST",
                f"issue/{issue_key}/transitions",
                {"transition": {"id": transition_id}},
            )
            logger.info("Transitioned %s to %s", issue_key, target)
            return True

        logger.warning("Transition '%s' not found for %s", target, issue_key)
        return False
