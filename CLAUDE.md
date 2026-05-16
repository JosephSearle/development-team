# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Layout

A **uv workspace** with 15 Python packages (Python 3.12+). The workspace root contains no source code — only the workspace coordinator `pyproject.toml`. All packages live under `shared/` (3 packages) and `agents/` (12 specialist agents + 1 orchestrator).

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

# Run all shared package tests
uv run pytest shared/state/tests -v

# Run a specific agent's tests
uv run pytest agents/orchestrator/tests -v

# Run a single test by name
uv run pytest agents/orchestrator/tests -v -k "test_routing"

# Lint
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .

# Type-check shared packages
uv run mypy shared/

# Type-check a specific agent
uv run mypy agents/orchestrator/src

# Full local CI check (matches the lint → typecheck → unit-test pipeline)
uv run ruff check . && uv run mypy shared/ && uv run pytest shared/state/tests
```

## TDD Convention

All code follows strict **Red → Green → Refactor**. This is structurally enforced by the LangGraph state machine: the Code Agent cannot commit code that has not first passed through the Test Agent's RED phase.

1. **RED**: Write the failing test first. Confirm it fails with `uv run pytest`.
2. **GREEN**: Write the minimum implementation to make it pass.
3. **REFACTOR**: Run `uv run ruff check --fix . && uv run mypy shared/` to clean.

Never write implementation before the test.

## Adding a New Workspace Member

1. Create directory under `shared/` or `agents/`
2. Add `pyproject.toml` with `[build-system]` using `hatchling`
3. Add `src/<module_name>/__init__.py` and a `py.typed` marker
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

## Architecture

### Agent Domains and Model Tiers

| Domain | Agents | Model |
|---|---|---|
| **Orchestration** | Orchestrator (raw `StateGraph` supervisor) | Qwen3.5-72B (reasoning) |
| **Development** | Code Agent, Test Agent, Code Review Agent | Qwen2.5-Coder-32B + LoRA (code) |
| **Engineering** | Git, CI/CD, Security, Infrastructure | Qwen2.5-14B (utility) |
| **Intelligence** | Architecture, Docs, Dependency, Incident Response | Qwen3.5-72B or Qwen2.5-14B |
| **Guardrail** | Input/output screening (all agents) | Llama-Guard-3-8B |

### Orchestrator vs Specialist Agents

- **Orchestrator** (`agents/orchestrator/`) is a raw LangGraph `StateGraph` with 6 nodes: `input_guardrail` → `task_planner` → `agent_router` → `hitl_gate` → specialist invoke nodes → `context_summariser`. Entry point: `build_orchestrator_graph()`.
- **Specialist agents** use `deepagents>=0.6.1` (`create_deep_agent()`). Each exports a `build_<agent>_graph()` function from its `__init__.py`.

### Standard Agent Package Structure

```
agents/<agent_name>/
├── pyproject.toml
├── src/<agent_name>/
│   ├── __init__.py          # exports build_<agent>_graph()
│   ├── graph.py             # LangGraph StateGraph builder
│   ├── schema.py            # Agent-specific TypedDict state
│   ├── nodes/               # One file per LangGraph node
│   └── prompts/             # Prompt templates
└── tests/
    ├── conftest.py
    ├── test_graph.py        # Compilation, routing, state transitions
    └── test_schema.py       # TypedDict serialization
```

### Canonical State Schema

`OrchestratorState` lives in `shared/state/src/dev_team_state/schema.py`. Schema changes require updating tests first. Key enums: `TaskStatus`, `TDDPhase` (SETUP/RED/GREEN/REFACTOR). Key types: `Subtask`, `AgentResult`, `HITLApproval`.

### Key Design Rules

- **DeepAgents v0.6.1+**: All 12 specialist agents use `create_deep_agent()`. The Orchestrator is a raw `StateGraph`.
- **HITL gates**: Use `langgraph.types.interrupt()` — never bypass with conditional logic. Gates trigger for: main-branch merges, production deployments, architectural decisions (ADRs), production infrastructure changes, Security Agent flags.
- **MCP only**: No agent calls external APIs directly. All external access goes through `langchain-mcp-adapters` + MCP server containers (GitHub, Jira, SonarQube, Jenkins, Slack, Context7, Kubernetes).
- **No credentials in state**: Secrets are injected via environment variables and consumed by MCP server containers only.
- **Type safety**: All state is `TypedDict`, mypy strict mode is enforced across all 15 packages, every package has a `py.typed` marker.

### Checkpointing

The Orchestrator uses `InMemorySaver()` by default; production passes a Redis checkpointer via `build_orchestrator_graph(checkpointer=...)`. Shared package: `shared/state/src/dev_team_state/checkpointer.py`.

## Shared Packages

| Package | Import name | Purpose |
|---|---|---|
| `shared/state` | `dev-team-state` | `OrchestratorState` schema, Redis checkpointer |
| `shared/mcp` | `dev-team-mcp` | `MCPRegistry` — builds `MultiServerMCPClient` from env URLs |
| `shared/guardrail` | `dev-team-guardrail` | `GuardrailClient` — async Llama-Guard-3 screening via httpx |

## CI Pipeline

`.github/workflows/ci.yml` runs 5 jobs on every push and PR:

1. **Lint** — `ruff check .` (line length 100, rules: E/F/I/UP/B/SIM/ANN)
2. **Type Check** (needs: lint) — `mypy` on all 3 shared packages and all 12 agents, strict mode
3. **Unit Tests** (needs: typecheck) — all agent and shared test directories, 80% coverage threshold
4. **Integration Tests** (needs: unit-test) — `tests/integration/`, 120 s timeout, 70% coverage on orchestrator
5. **Kubernetes Manifest Validation** (needs: lint) — `kubeconform` on `infra/kubernetes/`, CRDs ignored

## Local Development Environment Variables

For local development, copy `.env.example` to `.env`. Key variables:

| Variable | Description |
|---|---|
| `OPENAI_BASE_URL` | vLLM reasoning endpoint (Qwen3.5-72B) |
| `CODE_MODEL_BASE_URL` | vLLM code endpoint (Qwen2.5-Coder-32B) |
| `UTILITY_MODEL_BASE_URL` | vLLM utility endpoint (Qwen2.5-14B) |
| `GUARDRAIL_MODEL_BASE_URL` | vLLM guardrail endpoint (Llama-Guard-3-8B) |
| `REDIS_URL` | Redis Sentinel URL for the LangGraph checkpointer |
| `LANGCHAIN_TRACING_V2` | Set `true` to enable LangSmith tracing |
| `LANGCHAIN_ENDPOINT` / `LANGCHAIN_API_KEY` / `LANGCHAIN_PROJECT` | Self-hosted LangSmith |
| `HITL_APPROVAL_WEBHOOK` | Webhook URL the HITL gate calls for human approval |
| `GITHUB_MCP_URL` / `JIRA_MCP_URL` / `SONAR_MCP_URL` / `JENKINS_MCP_URL` / `SLACK_MCP_URL` | MCP server container URLs |

In production, all secrets are injected by the HashiCorp Vault Agent Injector sidecar.
