# Implementation Plan: Agentic Development Team

## Context

This plan governs the implementation of the Agentic Development Team — an autonomous 12-agent AI system that writes, tests, reviews, and deploys code. The architecture is fully specified across 10 C4 documents, 6 ADRs, and this plan.

**DeepAgents version:** `deepagents>=0.6.1`. This plan is fully reconciled against the deepagents 0.6.2 documentation, all C4 architecture documents, and all 6 ADRs.

**Why the rehaul (May 2026):** Earlier phase 3 drafts treated `create_deep_agent` as a dumb LLM wrapper (`tools=[]`, manual context-fetching nodes, code extracted from AIMessage strings). DeepAgents 0.6.2 provides built-in filesystem tools (`grep`, `glob`, `read_file`, `write_file`), `FilesystemBackend`, `FilesystemPermission`, `SummarizationMiddleware`, `skills`, `memory`, and `AsyncSubAgent` — none of which were used. The codebase search via Milvus required pre-indexing every repository and did not scale; agents now use built-in grep/glob instead.

---

## Design Principles (enforced across all phases)

1. **One deepagents harness per specialist agent.** The agent drives its own workflow. Manual LangGraph nodes are reserved for deterministic logic only (guardrails, subprocess execution, phase gates, scan gates).
2. **Never `tools=[]` without FilesystemBackend.** Every `create_deep_agent` call receives either MCP tools, or relies on built-in filesystem tools via `FilesystemBackend`. The agent decides when to use them.
3. **FilesystemBackend for all file-writing agents.** Agents write real files via `write_file`; the orchestrating node reads back from disk. Code is never extracted from AIMessage strings.
4. **No Milvus in the agent runtime path.** Codebase search uses built-in `grep`/`glob` on live files. Milvus StatefulSet remains in infrastructure for future use but is removed from all agent call paths.
5. **Every specialist agent has a skill.** Skills provide domain expertise as progressive-disclosure SKILL.md files, saving tokens vs. inline system prompt padding.
6. **SummarizationMiddleware on every specialist agent.** Long sessions need automatic context management. File-writing agents use `deepagents.middleware.SummarizationMiddleware` (with backend); reasoning-only agents use `langchain.agents.middleware.SummarizationMiddleware` (no backend needed).
7. **deepagents version `>=0.6.1` everywhere.** Ensures `ModelRetryMiddleware`, `ToolRetryMiddleware`, `SummarizationMiddleware`, `FilesystemBackend`, `FilesystemPermission`, `skills`, and `AsyncSubAgent` are available.
8. **Orchestrator stays a raw StateGraph.** It is the supervisor, not a specialist. It enforces typed state contracts and HITL gates that must not be bypassable by the harness.

---

## DeepAgents 0.6.2 — System-Wide Patterns

### Standard specialist agent template (file-writing agents)

```python
from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware  # deepagents version (needs backend)
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware
from langchain.chat_models import init_chat_model
from pathlib import Path

model = init_chat_model("openai:<model>", base_url=VLLM_URL, api_key="EMPTY", temperature=0)
backend = FilesystemBackend(root_dir=str(workspace), virtual_mode=False)

agent = create_deep_agent(
    model=model,
    tools=tools,                              # MCP tools from MCPRegistry
    system_prompt=SYSTEM_PROMPT,
    backend=backend,
    permissions=[
        FilesystemPermission(operations=["read", "write"], paths=[f"{workspace}/**"], mode="allow"),
        FilesystemPermission(operations=["write"], paths=["/**/.env", "/**/secrets/**", "/**/*.key", "/**/*.pem"], mode="deny"),
    ],
    middleware=[
        ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
        ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
        SummarizationMiddleware(model=model, backend=backend),
    ],
    skills=[str(Path(__file__).parent.parent / "skills")],
    name="<agent_name>",
)
```

### Standard specialist agent template (reasoning-only agents)

```python
from langchain.agents.middleware import ModelRetryMiddleware, SummarizationMiddleware, ToolRetryMiddleware

model = init_chat_model(...)

agent = create_deep_agent(
    model=model,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
        ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
        SummarizationMiddleware(model=model),   # langchain version, no backend needed
    ],
    skills=[str(Path(__file__).parent.parent / "skills")],
    name="<agent_name>",
)
```

### Skills directory (every agent)

```
agents/<agent_name>/src/<module>/
└── skills/
    └── <skill-name>/
        └── SKILL.md
```

SKILL.md frontmatter:
```yaml
---
name: <skill-name>
description: <≤1024 chars — LLM uses this to decide relevance>
allowed-tools: [read_file, write_file, grep, glob, ...]
---
```

### AsyncSubAgent (Architecture Agent, Incident Response Agent)

```python
from deepagents import AsyncSubAgent, create_deep_agent

subagent = AsyncSubAgent(
    name="<subagent_name>",
    description="<what it does>",
    graph_id="<graph_id>",   # ASGI in-process transport (no url = co-deployed)
)
agent = create_deep_agent(..., subagents=[subagent])
```

### interrupt_on (tool-level HITL within deepagents harness)

```python
agent = create_deep_agent(
    ...,
    interrupt_on={"<tool_name>": True},
    checkpointer=checkpointer,
)
```

---

## Repository Structure

```
development-team/
├── pyproject.toml          ← uv workspace root
├── uv.lock
├── CLAUDE.md
├── .github/workflows/ci.yml
├── docs/architecture/
├── shared/
│   ├── state/              ← OrchestratorState, TDDPhase, TestRunResult, CodeReviewResult
│   ├── guardrail/          ← GuardrailClient (Llama-Guard-3-8B HTTP client)
│   └── mcp/                ← MCPRegistry (MultiServerMCPClient factory)
└── agents/
    ├── orchestrator/       ← LangGraph StateGraph supervisor
    ├── test_agent/         ← TDD test writer + runner
    ├── code_agent/         ← TDD code writer + refactorer
    ├── code_review_agent/  ← Security-gated code reviewer
    ├── git_agent/
    ├── security_agent/
    ├── cicd_agent/
    ├── architecture_agent/
    ├── docs_agent/
    ├── infrastructure_agent/
    ├── dependency_agent/
    └── incident_response_agent/
```

---

## MCP Registry (`shared/mcp/src/dev_team_mcp/registry.py`)

Registered servers (milvus, postgres, argocd removed; slack added):

```python
_KNOWN_SERVERS = {"github", "jira", "context7", "sonarqube", "jenkins", "slack"}
```

Empty `server_names=[]` returns an empty `MultiServerMCPClient` (agents using only built-in filesystem tools pass `tools=[]`).

---

## Phase 0 — Foundation ✅ COMPLETE

`uv sync --locked --all-extras --dev` clean; schema tests pass; ruff + mypy clean.

---

## Phase 1 — Shared Infrastructure ✅ COMPLETE

GuardrailClient, MCPRegistry (updated server set), Redis checkpointer factory, shared state schema all correct.

---

## Phase 2 — Orchestrator ✅ COMPLETE

Raw `StateGraph` supervisor with HITL gate, task planner, agent router, context summariser, and input guardrail. Stub nodes (`invoke_code_agent`, etc.) replaced with real deepagents invocations in Phases 3–5.

---

## Phase 3 — Development Domain ✅ COMPLETE

### 3a — Code Agent

**Graph:** `START → code_agent_node → output_guardrail → END`

**Model:** Code (qwen2.5-coder-32b-instruct, multi-LoRA, 1×A100)
**MCP tools:** `MCPRegistry.build_client(["context7"])` — agent fetches library docs on demand
**FilesystemBackend:** workspace for implementation files
**Skill:** `skills/tdd-implementation/SKILL.md`
**Gate logic:** returns `{}` if `tdd_phase ∉ {RED, REFACTOR}`; fails after 5 iterations
**File read-back:** node reads `workspace/src/implementation.py` after agent completes
**output_guardrail:** regex scan for secrets patterns (sync, deterministic)

### 3b — Test Agent

**Graph:** `START → test_writer → test_runner → coverage_checker → flake_detector → END`

`test_runner`, `coverage_checker`, `flake_detector` remain manual nodes (subprocess/deterministic).

**test_writer:** `create_deep_agent` with `FilesystemBackend`, no MCP tools (built-in filesystem tools only), `skills/tdd-test-writing/SKILL.md`, `SummarizationMiddleware(model, backend)`
**File read-back:** node reads `workspace/tests/test_feature.py`; validates syntax before returning

### 3c — Code Review Agent

**Graph:** `START → scan_gate → [scan_complete→reviewer|END] → END`

**scan_gate:** deterministic check — scans `agent_results` for `security_agent*` entry with `scan_complete=True`

**reviewer:** `create_deep_agent` with GitHub MCP tools (`MCPRegistry.build_client(["github"])`), `skills/code-review/SKILL.md`, `SummarizationMiddleware(model)` (langchain version — no FilesystemBackend)
**Output:** JSON `CodeReviewResult` parsed from last AIMessage; `approved=True → status=completed`, `False → awaiting_approval`

### Verification

```bash
uv run pytest agents/test_agent/tests/ agents/code_agent/tests/ agents/code_review_agent/tests/ \
  -v --cov=test_agent --cov=code_agent --cov=code_review_agent --cov-fail-under=80
uv run ruff check agents/test_agent/src agents/code_agent/src agents/code_review_agent/src
uv run mypy agents/test_agent/src agents/code_agent/src agents/code_review_agent/src
```

---

## Phase 4 — Engineering Domain

All four agents: one `create_deep_agent` harness + deterministic output_guardrail or gate node + skill per agent.

### 4a — Git Agent

**Model:** Utility (qwen2.5-14b)
**MCP tools:** `MCPRegistry.build_client(["github"])`
**No FilesystemBackend** — all I/O through GitHub MCP
**Skill:** `skills/git-conventions/SKILL.md`
**interrupt_on:** `{"create_pull_request": True}` — pause before opening a PR

**Graph:** `START → git_agent_node → END`

```toml
dependencies = ["langgraph>=0.3", "langchain>=0.3", "langchain-core>=0.3",
                "langchain-openai>=0.3", "deepagents>=0.6.1", "dev-team-state", "dev-team-mcp"]
```

### 4b — Security Agent

**Model:** Utility (qwen2.5-14b) for analysis; Guardrail (Llama-Guard-3-8B) for classification
**MCP tools:** `MCPRegistry.build_client(["sonarqube", "github"])`
**Skill:** `skills/security-scanning/SKILL.md`
**interrupt_on:** `{"sonarqube_set_quality_gate": True}`

**Graph:** `START → secrets_scanner → sast_agent_node → output_guardrail → END`

`secrets_scanner` (sync): regex scan of diff — short-circuits to END (status=failed) on Critical/High hits without LLM call.

### 4c — CI/CD Agent

**Model:** Utility (qwen2.5-14b)
**MCP tools:** `MCPRegistry.build_client(["jenkins", "github"])`
**Skill:** `skills/cicd-patterns/SKILL.md`
**interrupt_on:** `{"trigger_production_deploy": True}`

**Graph:** `START → cicd_agent_node → END`

### 4d — Infrastructure Agent

**Model:** Utility (qwen2.5-14b)
**MCP tools:** `MCPRegistry.build_client(["github"])` (GitOps commits only — never ArgoCD write)
**FilesystemBackend:** workspace for manifest staging
**Skill:** `skills/k8s-conventions/SKILL.md`

**Graph:** `START → infrastructure_agent_node → END`

### Phase 4 Verification

```bash
uv run pytest agents/git_agent/tests/ agents/security_agent/tests/ \
  agents/cicd_agent/tests/ agents/infrastructure_agent/tests/ \
  -v --cov-fail-under=80
uv run ruff check agents/git_agent/src agents/security_agent/src \
  agents/cicd_agent/src agents/infrastructure_agent/src
uv run mypy agents/git_agent/src agents/security_agent/src \
  agents/cicd_agent/src agents/infrastructure_agent/src
```

---

## Phase 5 — Intelligence Domain

### 5a — Architecture Agent

**Model:** Reasoning (qwen3.5-72b)
**MCP tools:** `MCPRegistry.build_client(["context7", "github"])`
**FilesystemBackend:** workspace for ADR drafting
**AsyncSubAgent:** `library_researcher` for parallel library evaluation
**Skill:** `skills/adr-writing/SKILL.md`
**interrupt_on:** `{"commit_file": True}` — human approval before committing ADRs

**Graph:** `START → architecture_agent_node → END`

```python
library_researcher = AsyncSubAgent(
    name="library_researcher",
    description="Fetches and evaluates library documentation from Context7 for architecture evaluation",
    graph_id="library_researcher",
)
```

### 5b — Documentation Agent

**Model:** Utility (qwen2.5-14b)
**MCP tools:** `MCPRegistry.build_client(["github"])`
**FilesystemBackend:** workspace for doc drafting
**Skill:** `skills/documentation-standards/SKILL.md`

**Graph:** `START → docs_agent_node → END`

### 5c — Dependency Agent

**Model:** Utility (qwen2.5-14b)
**MCP tools:** `MCPRegistry.build_client(["github", "sonarqube"])`
**No FilesystemBackend** — operates on repo files via GitHub MCP
**Skill:** `skills/vulnerability-triage/SKILL.md`
**Deployment:** CronJob (daily), not a persistent Deployment

**Graph:** `START → dependency_agent_node → END`

### 5d — Incident Response Agent

**Model:** Reasoning (qwen3.5-72b)
**MCP tools:** `MCPRegistry.build_client(["github", "jira"])` + Kubernetes MCP (read-only)
**AsyncSubAgents:** `log_analyzer` + `metrics_analyzer` for parallel diagnostics
**Skill:** `skills/runbook-writing/SKILL.md`
**interrupt_on:** `{"create_jira_issue": True}`

**Graph:** `START → incident_agent_node → END`

```python
log_analyzer = AsyncSubAgent(name="log_analyzer", description="Analyse Kubernetes pod logs for error patterns", graph_id="log_analyzer")
metrics_analyzer = AsyncSubAgent(name="metrics_analyzer", description="Query Prometheus metrics for anomaly detection", graph_id="metrics_analyzer")
```

### Phase 5 Verification

```bash
uv run pytest agents/architecture_agent/tests/ agents/docs_agent/tests/ \
  agents/dependency_agent/tests/ agents/incident_response_agent/tests/ \
  -v --cov-fail-under=80
uv run ruff check agents/architecture_agent/src agents/docs_agent/src \
  agents/dependency_agent/src agents/incident_response_agent/src
uv run mypy agents/architecture_agent/src agents/docs_agent/src \
  agents/dependency_agent/src agents/incident_response_agent/src
```

---

## Phase 6 — Integration & End-to-End

Full TDD feature development loop with mocked vLLM endpoints. Additional test:

- **Skills loading integration test:** assert `skills/` resolves correctly at runtime per agent; SKILL.md readable; description ≤1024 chars

---

## Phase 7 — Infrastructure & Deployment ✅ COMPLETE

- **Remove Milvus** from `dev-team-agents` namespace — done; Milvus StatefulSet in `dev-team-platform` with internal headless Service only (no agent-facing Service)
- **All agent Deployments** in `infra/kubernetes/agents/deployments/` reference `registry.internal/dev-team/<agent>:latest` images; `deepagents>=0.6.1` installed via `uv sync --frozen` at image build time
- **Full manifest set** written to `infra/kubernetes/`:
  - `namespaces/` — 3 Namespace resources
  - `agents/` — ServiceAccounts, RBAC, NetworkPolicies, 12 Deployments/CronJob, 6 MCP server Deployments+Services, 5 KEDA ScaledObjects
  - `inference/` — 4 KServe InferenceService resources (Reasoning, Code+LoRA, Utility, Guardrail)
  - `platform/` — Redis StatefulSet+Sentinel+PDB, LangSmith StatefulSet, Milvus StatefulSet
- **CI job `validate-manifests`** added to `.github/workflows/ci.yml` (runs parallel to integration tests)

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| One deepagents harness per specialist agent | Agent drives its own workflow; manual nodes only for deterministic logic |
| Built-in grep/glob replaces Milvus codebase search | Works on any live repo without pre-indexing pipeline; always current |
| FilesystemBackend for file-writing agents | Agent writes real files; orchestrating node reads back from disk; no string extraction from AIMessage |
| Context7 MCP tools passed to create_deep_agent | Agent fetches library docs on demand, only for libraries it needs |
| Skills on every specialist agent | Progressive-disclosure domain expertise; saves tokens vs. always-on system prompt padding |
| deepagents SummarizationMiddleware for file-writing agents | Requires backend for history offloading; file-writing agents already have a FilesystemBackend |
| langchain SummarizationMiddleware for reasoning-only agents | No backend needed; simpler setup for agents that don't write files |
| AsyncSubAgent for Architecture + Incident Response | Parallel sub-tasks (library eval, log analysis, metrics queries) without blocking parent context |
| interrupt_on for destructive tool calls | Belt-and-suspenders HITL within the harness for sensitive tool invocations |
| Orchestrator stays raw StateGraph | Must enforce typed state contracts and HITL gates across sub-agent boundaries |
| deepagents>=0.6.1 everywhere | SummarizationMiddleware, FilesystemBackend, FilesystemPermission, skills all require ≥0.5.0 |
| MCPRegistry allows empty server_names | Agents using only built-in filesystem tools pass tools=[]; registry returns empty client |

---

## Implementation Order

### Phase 3 ✅ COMPLETE
1. Code Agent: deleted old 5-node pipeline; implemented `code_agent_node` + `output_guardrail`; `skills/tdd-implementation/`
2. Test Agent: replaced `init_chat_model` direct call in `test_writer` with `create_deep_agent` + `FilesystemBackend`; `skills/tdd-test-writing/`
3. Code Review Agent: added GitHub MCP tools + `SummarizationMiddleware` + `skills/code-review/` to `reviewer`
4. MCPRegistry: removed milvus/postgres/argocd; added slack; empty list returns empty client

### Phase 4 (next)
- Git Agent → Security Agent → CI/CD Agent → Infrastructure Agent
- Each: schema → skill → agent node → graph → tests → ruff + mypy

### Phase 5
- Architecture Agent → Docs Agent → Dependency Agent → Incident Response Agent
- Each: schema → skill → agent node → graph → tests → ruff + mypy

---

## Verification Plan (full system)

| Phase | Command | Pass Criteria |
|---|---|---|
| 3 | `uv run pytest agents/test_agent/tests/ agents/code_agent/tests/ agents/code_review_agent/tests/ -v --cov-fail-under=80` | All green ≥80% cov |
| 4 | `uv run pytest agents/git_agent/tests/ agents/security_agent/tests/ agents/cicd_agent/tests/ agents/infrastructure_agent/tests/ -v --cov-fail-under=80` | All green |
| 5 | `uv run pytest agents/architecture_agent/tests/ agents/docs_agent/tests/ agents/dependency_agent/tests/ agents/incident_response_agent/tests/ -v --cov-fail-under=80` | All green |
| All | `uv run ruff check . && uv run mypy shared/ agents/*/src` | Zero violations |
| 6 | `uv run pytest tests/integration/ -v --timeout=120` | Full loop green |
| 7 | `find infra/kubernetes -name "*.yaml" \| xargs kubeconform -strict -ignore-missing-schemas -summary` | 0 invalid, 0 errors (CRD resources skipped) |
