"""Jira integration -- create/update issues, watch for new tickets, validate completeness."""
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
    "review": "In Review",
}

# Fields the PM agent expects to be filled in a Jira ticket
REQUIRED_FIELDS = [
    "summary",
    "description",
    "priority",
    "issuetype",
]


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

    # --- Watcher: fetch new/updated tickets ---

    def fetch_assigned_issues(
        self, assignee: str | None = None, status: str = "To Do"
    ) -> list[dict]:
        """Fetch issues assigned to a user/bot in a given status.

        Args:
            assignee: Jira username or account ID. Defaults to JIRA_ASSIGNEE env var.
            status: Jira status to filter (default: "To Do").

        Returns:
            List of issue dicts with key, summary, description, priority, status.
        """
        assignee = assignee or os.getenv("JIRA_ASSIGNEE", "")
        if not assignee:
            logger.warning("No JIRA_ASSIGNEE configured, cannot watch tickets")
            return []

        jql = (
            f'project = "{self.project_key}" '
            f'AND assignee = "{assignee}" '
            f'AND status = "{status}" '
            f"ORDER BY created DESC"
        )
        import urllib.parse
        encoded_jql = urllib.parse.quote(jql)
        result = self._request("GET", f"search?jql={encoded_jql}&maxResults=50")
        if not result:
            return []

        issues = []
        for item in result.get("issues", []):
            fields = item.get("fields", {})
            desc_text = self._extract_text(fields.get("description"))
            issues.append({
                "key": item["key"],
                "summary": fields.get("summary", ""),
                "description": desc_text,
                "priority": fields.get("priority", {}).get("name", "Medium"),
                "status": fields.get("status", {}).get("name", ""),
                "issue_type": fields.get("issuetype", {}).get("name", "Task"),
                "reporter": fields.get("reporter", {}).get("displayName", ""),
            })
        return issues

    def get_issue(self, issue_key: str) -> dict | None:
        """Get full issue details."""
        result = self._request("GET", f"issue/{issue_key}")
        if not result:
            return None
        fields = result.get("fields", {})
        return {
            "key": result["key"],
            "summary": fields.get("summary", ""),
            "description": self._extract_text(fields.get("description")),
            "priority": fields.get("priority", {}).get("name", "Medium"),
            "status": fields.get("status", {}).get("name", ""),
            "issue_type": fields.get("issuetype", {}).get("name", "Task"),
            "reporter": fields.get("reporter", {}).get("displayName", ""),
            "acceptance_criteria": self._extract_text(
                fields.get("customfield_10100")  # Common AC field; adjust per instance
            ),
        }

    def get_comments(self, issue_key: str) -> list[dict]:
        """Get all comments on an issue."""
        result = self._request("GET", f"issue/{issue_key}/comment")
        if not result:
            return []
        comments = []
        for c in result.get("comments", []):
            comments.append({
                "id": c["id"],
                "author": c.get("author", {}).get("displayName", ""),
                "body": self._extract_text(c.get("body")),
                "created": c.get("created", ""),
            })
        return comments

    def validate_ticket_completeness(self, issue: dict) -> list[str]:
        """Check if a Jira ticket has all required information.

        Returns a list of missing/incomplete fields.
        """
        missing = []
        if not issue.get("summary", "").strip():
            missing.append("summary")
        if not issue.get("description", "").strip():
            missing.append("description")
        if len(issue.get("description", "")) < 20:
            missing.append("description (too short -- need more details)")
        if not issue.get("priority"):
            missing.append("priority")
        return missing

    @staticmethod
    def _extract_text(adf_content: dict | None) -> str:
        """Extract plain text from Atlassian Document Format (ADF)."""
        if not adf_content:
            return ""
        if isinstance(adf_content, str):
            return adf_content

        texts: list[str] = []

        def _walk(node: dict | list) -> None:
            if isinstance(node, list):
                for item in node:
                    _walk(item)
            elif isinstance(node, dict):
                if node.get("type") == "text":
                    texts.append(node.get("text", ""))
                for child in node.get("content", []):
                    _walk(child)

        _walk(adf_content)
        return "\n".join(texts)
