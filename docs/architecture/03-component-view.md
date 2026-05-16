# 03 — Component View

**Audience:** Engineers  
**C4 Level:** 3 — Component

This document provides component-level views of the two most architecturally significant containers: the **Orchestrator Agent** (the central hub of all system activity) and the **Development Domain** (the TDD loop between Code Agent and Test Agent). These are where the most complex internal coordination occurs.

---

## Orchestrator Agent — Component View

The Orchestrator Agent is a compiled LangGraph graph. Its internal components are the nodes and edges of that graph, plus supporting services injected at boot.

```mermaid
C4Component
  title Component View — Orchestrator Agent

  Container_Boundary(orchestrator, "Orchestrator Agent (Python / DeepAgents)") {
    Component(input_guard, "Input Guardrail", "LangGraph node / Llama-Guard-3-8B", "Screens all incoming task requests for prompt injection and policy violations before any processing begins")
    Component(task_planner, "Task Planner", "LangGraph node / Qwen3.5-72B", "Decomposes natural-language requirements into an ordered subtask graph using write_todos; maintains the master plan throughout execution")
    Component(router, "Agent Router", "LangGraph conditional edge", "Determines which specialist agent handles each subtask based on task type, current system state, and dependency graph")
    Component(hitl_gate, "Human-in-the-Loop Gate", "LangGraph interrupt node", "Pauses graph execution and awaits human approval for high-risk operations: production deploy, architecture decisions, main-branch merges")
    Component(sub_agent_spawner, "Sub-Agent Spawner", "DeepAgents task tool", "Instantiates specialist agent sub-graphs with isolated context windows; collects structured results and merges them back into master state")
    Component(state_manager, "State Manager", "LangGraph checkpointer / Redis", "Persists full graph state at every transition; enables failure recovery, time-travel debugging, and mid-task resume")
    Component(context_summariser, "Context Summariser", "SummarizationMiddleware / Qwen3.5-72B", "Auto-summarises context when the conversation window approaches the model's limit; large outputs are persisted to filesystem via FilesystemBackend")
  }

  ContainerDb(redis_checkpointer, "LangGraph Checkpointer", "Redis", "Persists graph state snapshots")
  Container(vllm_reason, "vLLM — Reasoning", "Qwen3.5-72B", "")
  Container(vllm_guard, "vLLM — Guardrail", "Llama-Guard-3-8B", "")

  Rel(input_guard, vllm_guard, "Classifies input safety", "REST")
  Rel(input_guard, task_planner, "Passes safe input", "LangGraph state")
  Rel(task_planner, vllm_reason, "LLM call for decomposition", "REST")
  Rel(task_planner, router, "Emits next subtask", "LangGraph state")
  Rel(router, hitl_gate, "Routes high-risk ops", "LangGraph edge")
  Rel(router, sub_agent_spawner, "Routes routine ops", "LangGraph edge")
  Rel(hitl_gate, sub_agent_spawner, "Resumes after approval", "LangGraph resume")
  Rel(sub_agent_spawner, state_manager, "Records delegation and result", "LangGraph state")
  Rel(state_manager, redis_checkpointer, "Persists snapshot", "TCP / Redis protocol")
  Rel(context_summariser, vllm_reason, "LLM call for summarisation", "REST")
```

### Internal Dependency Rules

- The Input Guardrail node is always the first node in every graph execution path. No LLM call or tool invocation may precede it.
- The Human-in-the-Loop Gate may only be bypassed by conditional edges that have been explicitly whitelisted in the router configuration.
- The Task Planner must not call any external tool directly. All external actions must flow through a specialist sub-agent.
- State snapshots are taken before and after every node execution. A node failure leaves the previous snapshot intact; the graph resumes from that snapshot on retry.
- The Context Summariser uses `SummarizationMiddleware` from DeepAgents (≥0.6.1) backed by `FilesystemBackend`. It does not rely on a separate summarisation pipeline.

---

## Development Domain — TDD Loop Component View

The TDD loop is the core value-delivery mechanism of the system. It is a structured cycle between the Code Agent and Test Agent, mediated by the Orchestrator.

```mermaid
C4Component
  title Component View — Development Domain (TDD Loop)

  Container_Boundary(dev_domain, "Development Domain") {

    Container_Boundary(code_container, "Code Agent (Python / DeepAgents)") {
      Component(context7_client, "Context7 Client", "MCP tool / langchain-mcp-adapters", "Queries current library documentation before writing code against any external API")
      Component(code_writer, "Code Writer", "LangGraph node / Qwen2.5-Coder-32B + LoRA", "Writes implementation code to pass failing tests; language selected by LoRA adapter tag")
      Component(code_refactor, "Code Refactorer", "LangGraph node / Qwen2.5-Coder-32B", "Refactors code for quality once tests pass; does not change behaviour")
      Component(code_search, "Codebase Search", "DeepAgents built-in grep/glob", "Searches existing codebase using built-in grep and glob tools against live files; prevents duplication without pre-indexing")
      Component(code_shell, "Shell Executor", "DeepAgents execute tool / sandboxed container", "Runs formatters (ruff, gofmt), linters, and build commands in an isolated container")
    }

    Container_Boundary(test_container, "Test Agent (Python / DeepAgents)") {
      Component(test_writer, "Test Writer", "LangGraph node / Qwen2.5-Coder-32B + LoRA", "Writes failing test stubs first (Red phase); validates tests are runnable and genuinely failing")
      Component(test_runner, "Test Runner", "DeepAgents execute tool / uv run", "Runs `uv run pytest`, `go test`, `mvn test`, etc. via shell; captures structured output")
      Component(coverage_checker, "Coverage Checker", "LangGraph node", "Asserts coverage meets configured thresholds; routes back to Code Agent if insufficient")
      Component(flake_detector, "Flake Detector", "LangGraph node", "Runs tests multiple times to identify intermittent failures; flags and quarantines flaky tests")
    }
  }

  Container(vllm_code, "vLLM — Code", "Qwen2.5-Coder-32B + LoRA", "")
  Container(git_agent, "Git Agent", "Python / DeepAgents", "")
  Container(security_agent, "Security Agent", "Python / DeepAgents", "")
  System_Ext(context7, "Context7", "")

  Rel(test_writer, vllm_code, "LLM call — write failing test", "REST")
  Rel(test_runner, test_writer, "Confirms test is Red", "LangGraph state")
  Rel(test_runner, code_writer, "Signals: tests failing — implement", "LangGraph state")
  Rel(context7_client, context7, "Fetch library docs", "MCP / REST")
  Rel(code_writer, context7_client, "Requests docs before coding", "internal")
  Rel(code_writer, code_search, "Searches for existing implementations", "internal")
  Rel(code_writer, vllm_code, "LLM call — write implementation", "REST")
  Rel(code_shell, test_runner, "Build output fed to test run", "LangGraph state")
  Rel(test_runner, coverage_checker, "Passes test results", "LangGraph state")
  Rel(coverage_checker, code_writer, "Routes back if coverage insufficient", "LangGraph edge")
  Rel(coverage_checker, code_refactor, "Routes to refactor if Green + covered", "LangGraph edge")
  Rel(code_refactor, vllm_code, "LLM call — refactor without breaking tests", "REST")
  Rel(code_refactor, test_runner, "Verify refactor is still Green", "LangGraph state")
  Rel(code_refactor, git_agent, "Signals: ready to commit", "LangGraph state")
  Rel(code_refactor, security_agent, "Signals: scan this diff", "LangGraph state")
```

### TDD Phase Transitions

The state machine enforces the Red → Green → Refactor sequence structurally — it is not a guideline:

1. **Red:** Test Writer produces tests; Test Runner confirms they fail. If tests pass immediately, the Test Writer is routed back to write more specific tests.
2. **Green:** Code Writer implements; Test Runner confirms all tests pass. If any test fails, Code Writer is re-invoked with the failure context.
3. **Refactor:** Code Refactorer improves code quality; Test Runner confirms no regression. If a regression is introduced, Code Refactorer is re-invoked with the diff and failure.
4. **Gate:** Security Agent scans the diff; Code Review Agent reviews; Git Agent commits and creates a PR.

A task does not exit the Development Domain until it is Green, Refactored, scanned, reviewed, and committed.

<!-- enriched by architecture-docs skill, 2026-05-15 -->
