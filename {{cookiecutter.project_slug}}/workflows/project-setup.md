# Project Setup

## Creating a New Project Workspace

```bash
mkdir -p projects/<YYYY-MM-DD-name>/{tasks,reviews,src,tests}
```

Or via CLI:
```bash
{{ cookiecutter.project_slug }} init <project-name>
```

## Required Files

| Step | Agent | File | Template |
|---|---|---|---|
| 1 | Tech Lead | `spec.md` + `tasks/TASK-001.md` | `projects/.templates/spec.md` |
| 2 | Architect | `architecture.md` | `projects/.templates/architecture.md` |
| 3 | Developer | `src/` | -- |
| 4 | Tester | `tests/` + `reviews/test-plan.md` | -- |

## Naming Convention
- Projects: `YYYY-MM-DD-short-description`
- Tasks: `TASK-NNN`
- Bugs: `BUG-NNN`
- Branches: `feat/TASK-NNN-short-desc` or `fix/BUG-NNN-short-desc`
