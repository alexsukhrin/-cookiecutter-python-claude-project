"""Base agent class wrapping Claude CLI."""
from __future__ import annotations

import logging
import re
import subprocess
import time
from dataclasses import dataclass, field

from .config import Config

logger = logging.getLogger(__name__)

# Per-role timeout overrides (seconds)
ROLE_TIMEOUTS: dict[str, int] = {
    "developer": 1800,
    "tester": 900,
    "architect": 900,
}
DEFAULT_TIMEOUT = 600

# Roles that modify code and need a working branch
CODE_ROLES = {"developer", "tester"}


def _slugify(text: str) -> str:
    """Convert text to a branch-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug[:50]


@dataclass
class Agent:
    """An agent that invokes Claude CLI with a specific role."""

    role: str
    config: Config = field(default_factory=Config)
    branch: str | None = None  # set by orchestrator for code-writing agents

    @property
    def system_prompt(self) -> str:
        """Load the agent's CLAUDE.md as system prompt."""
        return self.config.agent_prompt(self.role)

    @property
    def timeout(self) -> int:
        return ROLE_TIMEOUTS.get(self.role, DEFAULT_TIMEOUT)

    def run(self, prompt: str, task_id: str | None = None) -> str:
        """Run the agent with a prompt via Claude CLI.

        For code-writing roles (developer, tester), switches to the
        designated branch before running and commits changes after.

        Args:
            prompt: The user prompt / task description.
            task_id: Optional task ID for context.

        Returns:
            Claude CLI output as a string.
        """
        if task_id:
            prompt = f"[{task_id}] {prompt}"

        need_branch = self.role in CODE_ROLES and self.branch

        if need_branch:
            self._ensure_branch()

        cmd = self._build_command(prompt)
        logger.info("Running agent '%s': %s", self.role, prompt[:100])

        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.config.root),
                timeout=self.timeout,
            )
            duration = time.monotonic() - start

            if result.returncode != 0:
                logger.error(
                    "Agent '%s' failed (%.1fs): %s",
                    self.role, duration, result.stderr[:500],
                )
                raise AgentError(self.role, result.stderr)

            logger.info("Agent '%s' completed in %.1fs", self.role, duration)

            if need_branch:
                self._commit_changes()

            return result.stdout

        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start
            logger.error("Agent '%s' timed out after %.0fs", self.role, duration)
            raise AgentError(self.role, f"Timed out after {self.timeout} seconds")

    def _ensure_branch(self) -> None:
        """Create or switch to the task branch."""
        assert self.branch
        root = str(self.config.root)

        result = subprocess.run(
            ["git", "branch", "--list", self.branch],
            capture_output=True, text=True, cwd=root,
        )
        if self.branch in result.stdout:
            subprocess.run(
                ["git", "checkout", self.branch],
                capture_output=True, cwd=root,
            )
        else:
            subprocess.run(
                ["git", "checkout", "-b", self.branch],
                capture_output=True, cwd=root,
            )
        logger.info("Agent '%s' working on branch '%s'", self.role, self.branch)

    def _commit_changes(self) -> None:
        """Commit any changes made by the agent."""
        root = str(self.config.root)

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=root,
        )
        if not status.stdout.strip():
            logger.info("Agent '%s' made no file changes", self.role)
            return

        subprocess.run(["git", "add", "-A"], capture_output=True, cwd=root)
        subprocess.run(
            ["git", "commit", "-m",
             f"[{self.role}] Auto-commit from agent pipeline",
             "--no-verify"],
            capture_output=True, cwd=root,
        )
        logger.info(
            "Agent '%s' committed changes on branch '%s'",
            self.role, self.branch,
        )

    def _build_command(self, prompt: str) -> list[str]:
        """Build the Claude CLI command."""
        cmd = [
            "claude", "-p", prompt,
            "--system-prompt", self.system_prompt,
            "--allowedTools", "Read,Grep,Glob,Write,Edit,Bash",
            "--output-format", "text",
        ]
        if self.config.llm_model:
            cmd.extend(["--model", self.config.llm_model])
        if self.config.mcp_config_path.exists():
            cmd.extend(["--mcp-config", str(self.config.mcp_config_path)])
        return cmd


class AgentError(Exception):
    """Raised when an agent invocation fails."""

    def __init__(self, role: str, message: str) -> None:
        self.role = role
        super().__init__(f"Agent '{role}' error: {message}")
