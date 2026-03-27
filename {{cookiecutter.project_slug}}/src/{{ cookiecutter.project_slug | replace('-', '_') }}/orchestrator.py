"""Agent pipeline orchestrator."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .agent import Agent, AgentError
from .config import Config
from .integrations.hub import NotificationHub

logger = logging.getLogger(__name__)

ROLES = ("project-manager", "tech-lead", "architect", "developer", "tester")


@dataclass
class Pipeline:
    """Orchestrates the multi-agent validation pipeline."""

    config: Config = field(default_factory=Config)
    notifications: NotificationHub = field(default_factory=NotificationHub)

    def _agent(self, role: str) -> Agent:
        return Agent(role=role, config=self.config)

    def _run_step(self, step: str, role: str, prompt: str) -> str:
        """Run a single pipeline step with notifications."""
        logger.info("=== %s ===", step)
        self.notifications.on_step_start(step, role)
        try:
            result = self._agent(role).run(prompt)
            self.notifications.on_step_complete(step, role, result)
            return result
        except AgentError as e:
            self.notifications.on_step_failed(step, role, str(e))
            raise

    def run(self, request: str) -> dict[str, str]:
        """Run the full validation pipeline.

        Pipeline: PM -> Tech Lead -> Architect -> Tech Lead (validate)
                  -> Developer -> Architect (validate) -> Tester
                  -> Developer (fix) -> Tech Lead (sign-off) -> PM (close)

        Notifications are sent to all configured services (Slack, Jira,
        Linear, Telegram) at each step via the NotificationHub.
        """
        self.notifications.on_pipeline_start(request)
        results: dict[str, str] = {}

        try:
            results["pm_intake"] = self._run_step(
                "Step 1: PM Intake", "project-manager",
                f"Intake new request and create task file:\n\n{request}",
            )

            results["tl_decompose"] = self._run_step(
                "Step 2: Tech Lead Decompose", "tech-lead",
                f"Decompose into spec and subtasks:\n\n{results['pm_intake']}",
            )

            results["arch_design"] = self._run_step(
                "Step 3: Architect Design", "architect",
                f"Create architecture document:\n\n{results['tl_decompose']}",
            )

            results["tl_validate_arch"] = self._run_step(
                "Step 4: Tech Lead Validate Architecture", "tech-lead",
                f"Validate architecture for feasibility and scope:\n\n{results['arch_design']}",
            )

            results["dev_implement"] = self._run_step(
                "Step 5: Developer Implement", "developer",
                f"Implement according to approved architecture:\n\n"
                f"Spec: {results['tl_decompose']}\n\nArchitecture: {results['arch_design']}",
            )

            results["arch_validate_code"] = self._run_step(
                "Step 6: Architect Validate Code", "architect",
                f"Validate implementation matches design:\n\n{results['dev_implement']}",
            )

            results["tester_validate"] = self._run_step(
                "Step 7: Tester Validate", "tester",
                f"Create test plan and validate:\n\n"
                f"Spec: {results['tl_decompose']}\n\n"
                f"Implementation: {results['dev_implement']}",
            )

            results["tl_signoff"] = self._run_step(
                "Step 8: Tech Lead Sign-off", "tech-lead",
                f"Final sign-off review:\n\n"
                f"Test results: {results['tester_validate']}\n\n"
                f"Implementation: {results['dev_implement']}",
            )

            results["pm_close"] = self._run_step(
                "Step 9: PM Close", "project-manager",
                f"Close task and update tracking:\n\n{results['tl_signoff']}",
            )

            self.notifications.on_pipeline_complete(request)
        except AgentError as e:
            self.notifications.on_pipeline_failed(request, str(e))
            raise

        logger.info("=== Pipeline Complete ===")
        return results

    def run_fast_track(self, request: str) -> dict[str, str]:
        """Run simplified pipeline for S-complexity tasks."""
        self.notifications.on_pipeline_start(request)
        results: dict[str, str] = {}

        try:
            results["tl_task"] = self._run_step(
                "Fast: Tech Lead Task", "tech-lead",
                f"Create single task for small change:\n\n{request}",
            )

            results["dev_implement"] = self._run_step(
                "Fast: Developer Implement", "developer",
                f"Implement small change:\n\n{results['tl_task']}",
            )

            results["tester_validate"] = self._run_step(
                "Fast: Tester Validate", "tester",
                f"Minimal test coverage:\n\n{results['dev_implement']}",
            )

            results["tl_signoff"] = self._run_step(
                "Fast: Tech Lead Sign-off", "tech-lead",
                f"Sign off:\n\n{results['tester_validate']}",
            )

            self.notifications.on_pipeline_complete(request)
        except AgentError as e:
            self.notifications.on_pipeline_failed(request, str(e))
            raise

        return results
