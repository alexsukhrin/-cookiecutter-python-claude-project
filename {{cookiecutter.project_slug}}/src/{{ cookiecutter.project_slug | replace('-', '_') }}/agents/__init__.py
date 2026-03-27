"""Agent role implementations."""
from __future__ import annotations

from ..agent import Agent

AGENT_ROLES = {
    "business-analyst": "Ticket triage, business value assessment, priority, estimation",
    "project-manager": "Task intake, tracking, stakeholder communication",
    "tech-lead": "Decomposition, prioritization, final sign-off",
    "architect": "System design, data models, API contracts",
    "developer": "Implementation following architecture specs",
    "tester": "Validation, test plans, defect reporting",
}


def create_agent(role: str) -> Agent:
    """Create an agent by role name."""
    if role not in AGENT_ROLES:
        raise ValueError(f"Unknown role: {role}. Available: {list(AGENT_ROLES.keys())}")
    return Agent(role=role)
