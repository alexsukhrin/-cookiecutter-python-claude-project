"""Agent pipeline orchestrator."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .agent import Agent
from .config import Config

logger = logging.getLogger(__name__)

ROLES = ("project-manager", "tech-lead", "architect", "developer", "tester")


@dataclass
class Pipeline:
    """Orchestrates the multi-agent validation pipeline."""

    config: Config = field(default_factory=Config)

    def _agent(self, role: str) -> Agent:
        return Agent(role=role, config=self.config)

    def run(self, request: str) -> dict[str, str]:
        """Run the full validation pipeline.

        Pipeline: PM -> Tech Lead -> Architect -> Tech Lead (validate)
                  -> Developer -> Architect (validate) -> Tester
                  -> Developer (fix) -> Tech Lead (sign-off) -> PM (close)
        """
        results: dict[str, str] = {}

        # Step 1: PM intake
        logger.info("=== Step 1: Project Manager - Intake ===")
        results["pm_intake"] = self._agent("project-manager").run(
            f"Intake new request and create task file:\n\n{request}"
        )

        # Step 2: Tech Lead decomposition
        logger.info("=== Step 2: Tech Lead - Decompose ===")
        results["tl_decompose"] = self._agent("tech-lead").run(
            f"Decompose into spec and subtasks:\n\n{results['pm_intake']}"
        )

        # Step 3: Architect design
        logger.info("=== Step 3: Architect - Design ===")
        results["arch_design"] = self._agent("architect").run(
            f"Create architecture document:\n\n{results['tl_decompose']}"
        )

        # Step 4: Tech Lead validates architecture
        logger.info("=== Step 4: Tech Lead - Validate Architecture ===")
        results["tl_validate_arch"] = self._agent("tech-lead").run(
            f"Validate architecture for feasibility and scope:\n\n{results['arch_design']}"
        )

        # Step 5: Developer implements
        logger.info("=== Step 5: Developer - Implement ===")
        results["dev_implement"] = self._agent("developer").run(
            f"Implement according to approved architecture:\n\n"
            f"Spec: {results['tl_decompose']}\n\n"
            f"Architecture: {results['arch_design']}"
        )

        # Step 6: Architect validates code
        logger.info("=== Step 6: Architect - Validate Code ===")
        results["arch_validate_code"] = self._agent("architect").run(
            f"Validate implementation matches design:\n\n{results['dev_implement']}"
        )

        # Step 7: Tester validates
        logger.info("=== Step 7: Tester - Validate ===")
        results["tester_validate"] = self._agent("tester").run(
            f"Create test plan and validate:\n\n"
            f"Spec: {results['tl_decompose']}\n\n"
            f"Implementation: {results['dev_implement']}"
        )

        # Step 8: Tech Lead final sign-off
        logger.info("=== Step 8: Tech Lead - Sign Off ===")
        results["tl_signoff"] = self._agent("tech-lead").run(
            f"Final sign-off review:\n\n"
            f"Test results: {results['tester_validate']}\n\n"
            f"Implementation: {results['dev_implement']}"
        )

        # Step 9: PM closes
        logger.info("=== Step 9: Project Manager - Close ===")
        results["pm_close"] = self._agent("project-manager").run(
            f"Close task and update tracking:\n\n{results['tl_signoff']}"
        )

        logger.info("=== Pipeline Complete ===")
        return results

    def run_fast_track(self, request: str) -> dict[str, str]:
        """Run simplified pipeline for S-complexity tasks."""
        results: dict[str, str] = {}

        logger.info("=== Fast Track: Tech Lead ===")
        results["tl_task"] = self._agent("tech-lead").run(
            f"Create single task for small change:\n\n{request}"
        )

        logger.info("=== Fast Track: Developer ===")
        results["dev_implement"] = self._agent("developer").run(
            f"Implement small change:\n\n{results['tl_task']}"
        )

        logger.info("=== Fast Track: Tester ===")
        results["tester_validate"] = self._agent("tester").run(
            f"Minimal test coverage:\n\n{results['dev_implement']}"
        )

        logger.info("=== Fast Track: Tech Lead Sign-off ===")
        results["tl_signoff"] = self._agent("tech-lead").run(
            f"Sign off:\n\n{results['tester_validate']}"
        )

        return results
