Run the full agent pipeline for this request. Execute each step sequentially, using the full context from previous steps.

**Step 0 — BA Triage**: Read `agents/business-analyst/CLAUDE.md`. Evaluate business value, estimate complexity, decide Approved/Decline. If not Approved — stop here.

**Step 1 — PM Intake**: Read `agents/project-manager/CLAUDE.md`. Create task file in `tasks/`.

**Step 2 — Tech Lead Decompose**: Read `agents/tech-lead/CLAUDE.md`. Create spec in `projects/<name>/spec.md`.

**Step 3 — Architect Design**: Read `agents/architect/CLAUDE.md`. Create architecture in `projects/<name>/architecture.md`.

**Step 4 — Tech Lead Validate**: Validate architecture for feasibility and scope creep.

**Step 5 — Developer Implement**: Read `agents/developer/CLAUDE.md`. Create feature branch, implement, run linter+tests, commit.

**Step 6 — Tester Validate**: Read `agents/tester/CLAUDE.md`. Write tests, run them, report defects.

**Step 7 — Tech Lead Sign-off**: Review branch diff, verify quality, approve.

**Step 8 — PM Close**: Push branch, create MR, update task file to done.

Request: $ARGUMENTS