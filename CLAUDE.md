# CLAUDE.md — Agentic Development Team

This file is read by Claude Code at the start of every session.

## Repository Layout

A **uv workspace** with 15 Python packages. The workspace root contains no source code — only the workspace coordinator `pyproject.toml`. All packages live under `shared/` (3 packages) and `agents/` (12 packages).

## Toolchain

| Tool | Purpose | Command |
|---|---|---|
| uv | Package manager, virtual env | `uv sync --locked --all-extras --dev` |
| ruff | Linter + formatter | `uv run ruff check .` / `uv run ruff format .` |
| mypy | Static type checker | `uv run mypy shared/` |
| pytest | Test runner | `uv run pytest shared/state/tests -v` |

## Common Commands

```bash
# Install all workspace members including dev dependencies
uv sync --locked --all-extras --dev

# Run schema tests
uv run pytest shared/state/tests -v

# Run a specific agent's tests
uv run pytest agents/orchestrator/tests -v

# Lint
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .

# Type-check shared packages
uv run mypy shared/

# Type-check a specific agent
uv run mypy agents/orchestrator/src

# Full local CI check
uv run ruff check . && uv run mypy shared/ && uv run pytest shared/state/tests
```

## TDD Convention (enforced structurally in Phase 3+)

All code follows strict **Red → Green → Refactor**:

1. **RED**: Write the failing test first. Confirm it fails with `uv run pytest`.
2. **GREEN**: Write the minimum implementation to make it pass.
3. **REFACTOR**: Run `uv run ruff check --fix . && uv run mypy shared/` to clean.

Never write implementation before the test.

## Adding a New Workspace Member

1. Create directory under `shared/` or `agents/`
2. Add `pyproject.toml` with `[build-system]` using `hatchling`
3. Add `src/<module_name>/__init__.py`
4. Add `tests/__init__.py`
5. Register path in root `/pyproject.toml` `[tool.uv.workspace] members`
6. Run `uv lock` to update the lockfile
7. Run `uv sync --locked --all-extras --dev` to verify

## Inter-package Dependencies

```toml
# In agents/orchestrator/pyproject.toml:
[project]
dependencies = ["dev-team-state"]

[tool.uv.sources]
dev-team-state = { workspace = true }
```

## Key Design Decisions

- **DeepAgents v0.4.1**: Each of the 12 specialist agents is a `create_deep_agent()` instance. The Orchestrator is a raw LangGraph `StateGraph` supervisor.
- **OrchestratorState**: Canonical schema lives in `shared/state/src/dev_team_state/schema.py`. Schema changes require updating tests first.
- **HITL gates**: Use `langgraph.types.interrupt()` — never bypass with conditional logic.
- **MCP only**: No agent calls external APIs directly. All external access goes through `langchain-mcp-adapters` + MCP server containers.
- **No credentials in state**: All secrets are injected via environment variables and consumed by MCP server containers only.

## CI Pipeline

`.github/workflows/ci.yml` runs on every push and PR: lint → typecheck → unit-test → integration placeholder.
