"""Agent pipeline orchestrator."""
from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass, field

from .agent import Agent, AgentError, _slugify
from .config import Config
from .integrations.hub import NotificationHub

logger = logging.getLogger(__name__)

ROLES = (
    "business-analyst", "project-manager", "tech-lead",
    "architect", "developer", "tester", "devops",
)

# BA decision keywords in agent output
BA_APPROVED = "approved"
BA_NEEDS_INFO = "needs info"
BA_ON_HOLD = "on hold"
BA_DECLINE = "decline"


@dataclass
class StepResult:
    """Result of a single pipeline step."""

    step_name: str
    role: str
    output: str
    status: str  # "completed" | "failed"
    duration_s: float = 0.0


@dataclass
class Pipeline:
    """Orchestrates the multi-agent validation pipeline."""

    config: Config = field(default_factory=Config)
    notifications: NotificationHub = field(default_factory=NotificationHub)
    branch: str | None = None  # task branch for code-writing agents
    _original_branch: str | None = None

    def _agent(self, role: str) -> Agent:
        agent = Agent(role=role, config=self.config)
        if self.branch:
            agent.branch = self.branch
        return agent

    def _run_step(self, step: str, role: str, prompt: str) -> StepResult:
        """Run a single pipeline step with notifications."""
        logger.info("=== %s ===", step)
        self.notifications.on_step_start(step, role)

        start = time.monotonic()
        try:
            output = self._agent(role).run(prompt)
            duration = time.monotonic() - start
            result = StepResult(step, role, output, "completed", duration)
            self.notifications.on_step_complete(step, role, output)
            return result
        except AgentError as e:
            self.notifications.on_step_failed(step, role, str(e))
            raise

    def run(self, request: str) -> dict[str, StepResult]:
        """Run the full validation pipeline.

        Pipeline: BA (triage) -> PM -> Tech Lead -> Architect -> Tech Lead (validate)
                  -> Developer (on branch) -> Tester (on branch)
                  -> Tech Lead (sign-off) -> Push + MR -> PM (close)

        Developer and Tester agents work on a feature branch (agent/<slug>).
        Changes are auto-committed. A merge request is created automatically.
        """
        self.notifications.on_pipeline_start(request)
        results: dict[str, StepResult] = {}

        try:
            # BA Triage
            results["ba_triage"] = self._run_step(
                "Step 0: BA Triage", "business-analyst",
                f"Triage this request. Evaluate business value, estimate complexity, "
                f"assess priority, and decide (Approved / Needs Info / On Hold / Decline):\n\n{request}",
            )

            decision = self._parse_ba_decision(results["ba_triage"].output)
            logger.info("BA decision: %s", decision)

            if decision != BA_APPROVED:
                logger.info("Pipeline stopped: BA decision = %s", decision)
                return results

            results["pm_intake"] = self._run_step(
                "Step 1: PM Intake", "project-manager",
                f"Intake new request and create task file:\n\n{request}",
            )

            results["tl_decompose"] = self._run_step(
                "Step 2: Tech Lead Decompose", "tech-lead",
                f"Decompose into spec and subtasks:\n\n{results['pm_intake'].output}",
            )

            results["arch_design"] = self._run_step(
                "Step 3: Architect Design", "architect",
                f"Create architecture document:\n\n{results['tl_decompose'].output}",
            )

            results["tl_validate_arch"] = self._run_step(
                "Step 4: Tech Lead Validate Architecture", "tech-lead",
                f"Validate architecture for feasibility and scope:\n\n{results['arch_design'].output}",
            )

            # Create feature branch for code-writing agents
            self._create_task_branch(request)

            # Developer Implement (on task branch)
            results["dev_implement"] = self._run_step(
                "Step 5: Developer Implement", "developer",
                f"Implement according to approved architecture. "
                f"Run linter and tests after implementation.\n\n"
                f"Spec: {results['tl_decompose'].output}\n\n"
                f"Architecture: {results['arch_design'].output}",
            )

            # Tester Validate (on task branch)
            results["tester_validate"] = self._run_step(
                "Step 6: Tester Validate", "tester",
                f"Create test plan and validate implementation. "
                f"Run tests and verify all pass.\n\n"
                f"Spec: {results['tl_decompose'].output}\n\n"
                f"Implementation: {results['dev_implement'].output}",
            )

            # Return to original branch
            self._return_to_original_branch()

            # Tech Lead Sign-off (reviews the branch diff)
            branch_diff = self._get_branch_diff()
            results["tl_signoff"] = self._run_step(
                "Step 7: Tech Lead Sign-off", "tech-lead",
                f"Final sign-off. Review the branch diff and test results.\n\n"
                f"Branch: {self.branch}\n\n"
                f"Diff:\n{branch_diff}\n\n"
                f"Test results: {results['tester_validate'].output}\n\n"
                f"Implementation: {results['dev_implement'].output}",
            )

            # Push branch and create MR
            mr_url = self._push_and_create_mr(request)

            results["pm_close"] = self._run_step(
                "Step 8: PM Close", "project-manager",
                f"Close task. Update task file status to done.\n\n"
                f"Merge request: {mr_url or 'not created'}\n\n"
                f"Sign-off: {results['tl_signoff'].output}",
            )

            self.notifications.on_pipeline_complete(request, {
                k: v.output for k, v in results.items()
            })
        except AgentError as e:
            self.notifications.on_pipeline_failed(request, str(e))
            raise

        logger.info("=== Pipeline Complete ===")
        return results

    def run_fast_track(self, request: str) -> dict[str, StepResult]:
        """Run simplified pipeline for S-complexity tasks."""
        self.notifications.on_pipeline_start(request)
        results: dict[str, StepResult] = {}

        try:
            results["tl_task"] = self._run_step(
                "Fast: Tech Lead Task", "tech-lead",
                f"Create single task for small change:\n\n{request}",
            )

            self._create_task_branch(request)

            results["dev_implement"] = self._run_step(
                "Fast: Developer Implement", "developer",
                f"Implement small change:\n\n{results['tl_task'].output}",
            )

            results["tester_validate"] = self._run_step(
                "Fast: Tester Validate", "tester",
                f"Minimal test coverage:\n\n{results['dev_implement'].output}",
            )

            self._return_to_original_branch()

            results["tl_signoff"] = self._run_step(
                "Fast: Tech Lead Sign-off", "tech-lead",
                f"Sign off:\n\n{results['tester_validate'].output}",
            )

            mr_url = self._push_and_create_mr(request)
            logger.info("Fast track MR: %s", mr_url)

            self.notifications.on_pipeline_complete(request, {
                k: v.output for k, v in results.items()
            })
        except AgentError as e:
            self.notifications.on_pipeline_failed(request, str(e))
            raise

        return results

    def _parse_ba_decision(self, ba_output: str) -> str:
        """Extract BA decision from agent output."""
        output_lower = ba_output.lower()
        for keyword in (BA_DECLINE, BA_ON_HOLD, BA_NEEDS_INFO, BA_APPROVED):
            if keyword in output_lower:
                return keyword
        return BA_APPROVED

    def run_from_jira(self, issue_key: str) -> dict[str, StepResult]:
        """Run pipeline from an existing Jira ticket.

        Full flow:
        1. Fetch ticket from Jira
        2. BA triages: evaluate business value, estimate, priority, decide
        3. If BA approved -> full pipeline with branch + MR
        4. If BA needs info / on hold / decline -> comment in Jira, stop
        5. Publish results to Confluence
        """
        jira = self.notifications.jira
        if not jira.enabled:
            raise RuntimeError("Jira integration required for run_from_jira")

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

        return self.run(request_text)

    def watch_jira(self, assignee: str | None = None) -> list[dict[str, StepResult]]:
        """Watch Jira for new tickets and run pipeline for each."""
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

    # --- Branch management ---

    def _create_task_branch(self, request: str) -> None:
        """Create a feature branch for developer/tester agents."""
        root = str(self.config.root)

        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=root,
        )
        self._original_branch = result.stdout.strip()

        slug = _slugify(request)
        self.branch = f"agent/{slug}"

        logger.info(
            "Creating task branch '%s' from '%s'",
            self.branch, self._original_branch,
        )

    def _return_to_original_branch(self) -> None:
        """Switch back to the original branch."""
        if self._original_branch:
            subprocess.run(
                ["git", "checkout", self._original_branch],
                capture_output=True, cwd=str(self.config.root),
            )
            logger.info("Returned to branch '%s'", self._original_branch)

    def _get_branch_diff(self) -> str:
        """Get diff between task branch and original branch."""
        if not self.branch or not self._original_branch:
            return "(no branch diff available)"
        result = subprocess.run(
            ["git", "diff", f"{self._original_branch}...{self.branch}", "--stat"],
            capture_output=True, text=True, cwd=str(self.config.root),
        )
        return result.stdout or "(no changes)"

    def _push_and_create_mr(self, request: str) -> str | None:
        """Push task branch and create a merge request via git push options."""
        if not self.branch:
            return None

        root = str(self.config.root)
        target = self._original_branch or "master"

        # Push branch
        result = subprocess.run(
            ["git", "push", "-u", "origin", self.branch],
            capture_output=True, text=True, cwd=root,
        )
        if result.returncode != 0:
            logger.warning("Failed to push branch '%s': %s", self.branch, result.stderr[:300])
            return None
        logger.info("Pushed branch '%s'", self.branch)

        # Create MR via git push options (works with GitLab and some GitHub setups)
        title = request.split("\n")[0].strip()[:70]

        result = subprocess.run(
            [
                "git", "push",
                "-o", "merge_request.create",
                "-o", f"merge_request.title={title}",
                "-o", f"merge_request.target={target}",
                "origin", self.branch,
            ],
            capture_output=True, text=True, cwd=root,
        )

        # Extract MR URL from git push output
        mr_url = None
        for line in result.stderr.split("\n"):
            if "merge_requests" in line and "http" in line:
                for part in line.split():
                    if part.startswith("http") and "merge_requests" in part:
                        mr_url = part
                        break

        if mr_url:
            logger.info("Created merge request: %s", mr_url)
        else:
            logger.info("Branch pushed, MR may need manual creation")

        return mr_url

    def run_single(self, role: str, prompt: str) -> str:
        """Run a single agent (no pipeline)."""
        return self._agent(role).run(prompt)
