"""Base agent class wrapping Claude CLI."""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """An agent that invokes Claude CLI with a specific role."""

    role: str
    config: Config = field(default_factory=Config)

    @property
    def system_prompt(self) -> str:
        """Load the agent's CLAUDE.md as system prompt."""
        return self.config.agent_prompt(self.role)

    def run(self, prompt: str, task_id: str | None = None) -> str:
        """Run the agent with a prompt via Claude CLI.

        Args:
            prompt: The user prompt / task description.
            task_id: Optional task ID for context.

        Returns:
            Claude CLI output as a string.
        """
        if task_id:
            prompt = f"[{task_id}] {prompt}"

        cmd = self._build_command(prompt)
        logger.info("Running agent '%s': %s", self.role, prompt[:100])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.config.root),
                timeout=300,
            )
            if result.returncode != 0:
                logger.error("Agent '%s' failed: %s", self.role, result.stderr)
                raise AgentError(self.role, result.stderr)
            logger.info("Agent '%s' completed successfully", self.role)
            return result.stdout
        except subprocess.TimeoutExpired:
            raise AgentError(self.role, "Timed out after 300 seconds")

    def _build_command(self, prompt: str) -> list[str]:
        """Build the Claude CLI command."""
        cmd = ["claude", "-p", prompt, "--model", self.config.llm_model]
        if self.config.mcp_config_path.exists():
            cmd.extend(["--mcp-config", str(self.config.mcp_config_path)])
        return cmd


class AgentError(Exception):
    """Raised when an agent invocation fails."""

    def __init__(self, role: str, message: str) -> None:
        self.role = role
        super().__init__(f"Agent '{role}' error: {message}")
