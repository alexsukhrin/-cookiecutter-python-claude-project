"""Confluence integration -- create and update documentation pages."""
from __future__ import annotations

import base64
import json
import logging
import os
import urllib.request
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConfluenceClient:
    """Lightweight Confluence Cloud client using REST API v2 (no SDK dependency)."""

    base_url: str | None = None
    api_token: str | None = None
    user_email: str | None = None
    space_key: str = "{{ cookiecutter.confluence_space_key }}"
    _headers: dict = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url or os.getenv("CONFLUENCE_URL", "").rstrip("/")
        self.api_token = self.api_token or os.getenv("CONFLUENCE_API_TOKEN")
        self.user_email = self.user_email or os.getenv("CONFLUENCE_USER_EMAIL")
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

    def _request(
        self, method: str, path: str, data: dict | None = None
    ) -> dict | None:
        """Make an authenticated request to Confluence REST API."""
        if not self.enabled:
            logger.debug("Confluence not configured, skipping")
            return None

        url = f"{self.base_url}/wiki/api/v2/{path.lstrip('/')}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read()) if resp.status != 204 else {}
        except Exception as e:
            logger.error("Confluence API error (%s %s): %s", method, path, e)
            return None

    def _get_space_id(self) -> str | None:
        """Get space ID by space key."""
        result = self._request("GET", f"spaces?keys={self.space_key}")
        if result and result.get("results"):
            return result["results"][0]["id"]
        return None

    def create_page(
        self,
        title: str,
        body_html: str,
        parent_id: str | None = None,
    ) -> dict | None:
        """Create a Confluence page. Returns {id, title, _links.webui}.

        Args:
            title: Page title.
            body_html: HTML content for the page body.
            parent_id: Optional parent page ID for nesting.
        """
        space_id = self._get_space_id()
        if not space_id:
            logger.error("Confluence space not found: %s", self.space_key)
            return None

        payload: dict = {
            "spaceId": space_id,
            "status": "current",
            "title": title,
            "body": {
                "representation": "storage",
                "value": body_html,
            },
        }
        if parent_id:
            payload["parentId"] = parent_id

        result = self._request("POST", "pages", payload)
        if result and "id" in result:
            logger.info("Created Confluence page: %s (id=%s)", title, result["id"])
            return result
        return None

    def update_page(self, page_id: str, title: str, body_html: str, version: int) -> dict | None:
        """Update an existing Confluence page.

        Args:
            page_id: The page ID to update.
            title: Updated page title.
            body_html: Updated HTML content.
            version: Current version number (will be incremented).
        """
        result = self._request(
            "PUT",
            f"pages/{page_id}",
            {
                "id": page_id,
                "status": "current",
                "title": title,
                "body": {
                    "representation": "storage",
                    "value": body_html,
                },
                "version": {
                    "number": version + 1,
                    "message": "Updated by pipeline agent",
                },
            },
        )
        if result and "id" in result:
            logger.info("Updated Confluence page: %s", title)
        return result

    def find_page(self, title: str) -> dict | None:
        """Find a page by title in the configured space."""
        space_id = self._get_space_id()
        if not space_id:
            return None

        import urllib.parse
        encoded_title = urllib.parse.quote(title)
        result = self._request("GET", f"spaces/{space_id}/pages?title={encoded_title}")
        if result and result.get("results"):
            return result["results"][0]
        return None

    def publish_pipeline_results(
        self,
        task_title: str,
        spec: str,
        architecture: str,
        implementation: str,
        test_results: str,
        parent_id: str | None = None,
    ) -> dict | None:
        """Publish full pipeline results as a structured Confluence page.

        Creates or updates a documentation page with all pipeline artifacts.
        """
        body_html = f"""
        <h2>Specification</h2>
        <ac:structured-macro ac:name="code">
          <ac:parameter ac:name="language">markdown</ac:parameter>
          <ac:plain-text-body><![CDATA[{spec}]]></ac:plain-text-body>
        </ac:structured-macro>

        <h2>Architecture</h2>
        <ac:structured-macro ac:name="code">
          <ac:parameter ac:name="language">markdown</ac:parameter>
          <ac:plain-text-body><![CDATA[{architecture}]]></ac:plain-text-body>
        </ac:structured-macro>

        <h2>Implementation Summary</h2>
        <ac:structured-macro ac:name="code">
          <ac:parameter ac:name="language">markdown</ac:parameter>
          <ac:plain-text-body><![CDATA[{implementation}]]></ac:plain-text-body>
        </ac:structured-macro>

        <h2>Test Results</h2>
        <ac:structured-macro ac:name="code">
          <ac:parameter ac:name="language">markdown</ac:parameter>
          <ac:plain-text-body><![CDATA[{test_results}]]></ac:plain-text-body>
        </ac:structured-macro>

        <p><em>Auto-generated by pipeline agent</em></p>
        """

        existing = self.find_page(task_title)
        if existing:
            return self.update_page(
                existing["id"], task_title, body_html, existing["version"]["number"]
            )
        return self.create_page(task_title, body_html, parent_id)
