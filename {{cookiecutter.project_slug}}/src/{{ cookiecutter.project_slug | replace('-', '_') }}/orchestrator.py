"""Agent pipeline orchestrator."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .agent import Agent, AgentError
from .config import Config
from .integrations.hub import NotificationHub

logger = logging.getLogger(__name__)

ROLES = (
    "business-analyst", "project-manager", "tech-lead",
    "architect", "developer", "tester",
)

# BA decision keywords in agent output
BA_APPROVED = "approved"
BA_NEEDS_INFO = "needs info"
BA_ON_HOLD = "on hold"
BA_DECLINE = "decline"


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

            self.notifications.on_pipeline_complete(request, results)
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

            self.notifications.on_pipeline_complete(request, results)
        except AgentError as e:
            self.notifications.on_pipeline_failed(request, str(e))
            raise

        return results

    def _parse_ba_decision(self, ba_output: str) -> str:
        """Extract BA decision from agent output.

        Looks for 'Decision: <value>' in the output.
        Returns one of: approved, needs info, on hold, decline.
        Defaults to 'approved' if not found.
        """
        output_lower = ba_output.lower()
        for keyword in (BA_DECLINE, BA_ON_HOLD, BA_NEEDS_INFO, BA_APPROVED):
            if keyword in output_lower:
                return keyword
        return BA_APPROVED

    def run_from_jira(self, issue_key: str) -> dict[str, str]:
        """Run pipeline from an existing Jira ticket.

        Full flow:
        1. Fetch ticket from Jira
        2. BA triages: evaluate business value, estimate, priority, decide
        3. If BA approved -> PM validates completeness & enriches
        4. If BA needs info / on hold -> comment in Jira, return to reporter
        5. Full pipeline (TL -> Arch -> Dev -> Tester)
        6. Publish results to Confluence
        7. Transition Jira to "Review" for customer verification
        """
        jira = self.notifications.jira
        if not jira.enabled:
            raise RuntimeError("Jira integration required for run_from_jira")

        # 1. Fetch ticket
        logger.info("=== Fetching Jira ticket: %s ===", issue_key)
        issue = jira.get_issue(issue_key)
        if not issue:
            raise RuntimeError(f"Could not fetch Jira issue: {issue_key}")

        self.notifications.set_jira_issue(issue_key)

        request_text = (
            f"Jira Ticket: {issue_key}\n"
            f"Summary: {issue['summary']}\n"
            f"Description: {issue['description']}\n"
            f"Priority: {issue['priority']}\n"
            f"Reporter: {issue['reporter']}\n"
            f"Type: {issue['issue_type']}"
        )

        results: dict[str, str] = {}

        # 2. BA Triage -- evaluate value, estimate, decide
        logger.info("=== Step 0: Business Analyst - Triage ===")
        results["ba_triage"] = self._run_step(
            "Step 0: BA Triage", "business-analyst",
            f"Triage this Jira ticket. Evaluate business value, estimate "
            f"complexity and time, assess priority, and make a decision "
            f"(Approved / Needs Info / On Hold / Decline). "
            f"Write your analysis in the standard BA comment format.\n\n{request_text}",
        )

        # Post BA analysis as Jira comment
        jira.add_comment(issue_key, results["ba_triage"])

        # 3. Check BA decision
        decision = self._parse_ba_decision(results["ba_triage"])
        results["ba_decision"] = decision
        logger.info("BA decision for %s: %s", issue_key, decision)

        if decision == BA_NEEDS_INFO:
            jira.transition_issue(issue_key, "Waiting for Customer")
            logger.info("Ticket %s returned to reporter -- needs more info", issue_key)
            return results

        if decision == BA_ON_HOLD:
            jira.transition_issue(issue_key, "Waiting for Customer")
            jira.add_comment(
                issue_key,
                "This ticket has been put on hold for stakeholder review. "
                "Please evaluate whether this should proceed.",
            )
            logger.info("Ticket %s put on hold for customer review", issue_key)
            return results

        if decision == BA_DECLINE:
            jira.transition_issue(issue_key, "Won't Do")
            logger.info("Ticket %s declined by BA", issue_key)
            return results

        # 4. BA approved -> start full pipeline
        self.notifications.on_pipeline_start(request_text)

        try:
            # PM validates completeness and enriches
            missing = jira.validate_ticket_completeness(issue)
            if missing:
                question = (
                    f"Ticket {issue_key} is missing required information:\n"
                    + "\n".join(f"- {m}" for m in missing)
                    + "\n\nPlease provide the missing details."
                )
                jira.add_comment(issue_key, question)
                logger.warning("Ticket %s incomplete: %s", issue_key, missing)

            results["pm_intake"] = self._run_step(
                "Step 1: PM Validate & Enrich", "project-manager",
                f"Validate and enrich this Jira ticket. "
                f"BA has approved it with this analysis:\n{results['ba_triage']}\n\n"
                f"Check acceptance criteria. Create a local task file from "
                f"projects/.templates/task.md.\n\n{request_text}",
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
                f"Validate architecture:\n\n{results['arch_design']}",
            )

            results["dev_implement"] = self._run_step(
                "Step 5: Developer Implement", "developer",
                f"Implement according to approved architecture:\n\n"
                f"Spec: {results['tl_decompose']}\n\n"
                f"Architecture: {results['arch_design']}",
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
                "Step 9: PM Close & Document", "project-manager",
                f"Close task. Update Jira {issue_key}. "
                f"Summarize results for documentation.\n\n{results['tl_signoff']}",
            )

            # Pipeline complete -> Confluence docs + Jira to Review
            self.notifications.on_pipeline_complete(request_text, results)

        except AgentError as e:
            self.notifications.on_pipeline_failed(request_text, str(e))
            raise

        logger.info("=== Pipeline Complete for %s ===", issue_key)
        return results

    def watch_jira(self, assignee: str | None = None) -> list[dict[str, str]]:
        """Watch Jira for new tickets and run pipeline for each.

        Fetches all "To Do" tickets assigned to the configured user,
        and runs the full Jira-driven pipeline for each.

        Returns:
            List of results dicts, one per processed ticket.
        """
        jira = self.notifications.jira
        if not jira.enabled:
            raise RuntimeError("Jira integration required for watch_jira")

        issues = jira.fetch_assigned_issues(assignee=assignee)
        if not issues:
            logger.info("No new Jira tickets found")
            return []

        logger.info("Found %d new Jira ticket(s) to process", len(issues))
        all_results = []
        for issue in issues:
            try:
                result = self.run_from_jira(issue["key"])
                all_results.append(result)
            except Exception as e:
                logger.error("Failed to process %s: %s", issue["key"], e)

        return all_results
