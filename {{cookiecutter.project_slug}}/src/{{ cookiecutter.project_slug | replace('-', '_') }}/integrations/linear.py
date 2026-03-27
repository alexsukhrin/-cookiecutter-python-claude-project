"""Linear integration -- create and manage issues via GraphQL API."""
from __future__ import annotations

import json
import logging
import os
import urllib.request
from dataclasses import dataclass

logger = logging.getLogger(__name__)

LINEAR_API = "https://api.linear.app/graphql"

STATUS_MAP = {
    "draft": "Backlog",
    "in_review": "In Review",
    "approved": "Todo",
    "in_progress": "In Progress",
    "done": "Done",
}


@dataclass
class LinearClient:
    """Lightweight Linear client using GraphQL API (no SDK dependency)."""

    api_key: str | None = None
    team_key: str = "{{ cookiecutter.linear_workspace }}"

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.getenv("LINEAR_API_KEY")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _graphql(self, query: str, variables: dict | None = None) -> dict | None:
        """Execute a GraphQL query against Linear API."""
        if not self.enabled:
            logger.debug("Linear not configured, skipping")
            return None

        payload = json.dumps({"query": query, "variables": variables or {}}).encode()
        req = urllib.request.Request(
            LINEAR_API,
            data=payload,
            headers={
                "Authorization": self.api_key,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
                if "errors" in result:
                    logger.error("Linear GraphQL errors: %s", result["errors"])
                return result.get("data")
        except Exception as e:
            logger.error("Linear API error: %s", e)
            return None

    def get_team_id(self) -> str | None:
        """Get the team ID by key/slug."""
        data = self._graphql(
            """query($key: String!) {
                teams(filter: { key: { eq: $key } }) {
                    nodes { id name }
                }
            }""",
            {"key": self.team_key},
        )
        if data and data.get("teams", {}).get("nodes"):
            return data["teams"]["nodes"][0]["id"]
        return None

    def create_issue(
        self,
        title: str,
        description: str = "",
        priority: int = 3,
    ) -> dict | None:
        """Create a Linear issue. Returns {id, identifier, url}.

        Priority: 0=No, 1=Urgent, 2=High, 3=Medium, 4=Low
        """
        team_id = self.get_team_id()
        if not team_id:
            logger.error("Could not find Linear team: %s", self.team_key)
            return None

        data = self._graphql(
            """mutation($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue { id identifier url title }
                }
            }""",
            {
                "input": {
                    "teamId": team_id,
                    "title": title,
                    "description": description,
                    "priority": priority,
                }
            },
        )
        if data and data.get("issueCreate", {}).get("success"):
            issue = data["issueCreate"]["issue"]
            logger.info("Created Linear issue: %s (%s)", issue["identifier"], issue["url"])
            return issue
        return None

    def update_issue_status(self, issue_id: str, status: str) -> bool:
        """Update an issue's status by finding the matching workflow state."""
        target = STATUS_MAP.get(status, status)

        # Get workflow states for the issue's team
        states_data = self._graphql(
            """query {
                workflowStates {
                    nodes { id name }
                }
            }"""
        )
        if not states_data:
            return False

        state_id = None
        for state in states_data.get("workflowStates", {}).get("nodes", []):
            if state["name"].lower() == target.lower():
                state_id = state["id"]
                break

        if not state_id:
            logger.warning("Linear state '%s' not found", target)
            return False

        data = self._graphql(
            """mutation($id: String!, $input: IssueUpdateInput!) {
                issueUpdate(id: $id, input: $input) { success }
            }""",
            {"id": issue_id, "input": {"stateId": state_id}},
        )
        return bool(data and data.get("issueUpdate", {}).get("success"))

    def add_comment(self, issue_id: str, body: str) -> bool:
        """Add a comment to a Linear issue."""
        data = self._graphql(
            """mutation($input: CommentCreateInput!) {
                commentCreate(input: $input) { success }
            }""",
            {"input": {"issueId": issue_id, "body": body}},
        )
        return bool(data and data.get("commentCreate", {}).get("success"))
