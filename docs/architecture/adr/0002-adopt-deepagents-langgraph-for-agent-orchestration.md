# ADR 0002: Adopt DeepAgents + LangGraph for Agent Orchestration

**Date:** 2026-05-12  
**Status:** Accepted  
**Deciders:** Engineering team

## Context

The system requires a framework for building twelve specialist agents that can: decompose complex tasks, delegate subtasks to sub-agents, maintain state across multi-step executions, integrate with external tools via MCP, and support human-in-the-loop interruption at defined checkpoints. The framework must support Python (the primary agent runtime), be open-source (no vendor lock-in), and work with any LLM provider via a standard API.

The team needs a harness that is production-ready immediately, rather than requiring custom implementation of planning, filesystem access, context management, and sub-agent spawning. The framework must also provide native observability integration.

Constraints:
- Must work with OpenAI-compatible vLLM endpoints (self-hosted models)
- Must support MCP tool integration without custom adapters
- Must support human-in-the-loop without custom state machine implementation
- Must be MIT licensed or similarly permissive

## Decision

We will use **LangChain DeepAgents** (v0.6.x, pinned at `>=0.6.1`) as the agent harness for all twelve specialist agents, built on **LangGraph** v1.x as the underlying orchestration graph runtime.

## Rationale

DeepAgents provides out-of-the-box: planning tools (`write_todos`/`read_todos`), filesystem access, sandboxed shell execution, sub-agent spawning via the `task` tool, context auto-summarisation, and smart prompt defaults. These are the exact capabilities all twelve agents require. Building these from scratch on top of raw LangGraph would require significant custom implementation with no functional advantage.

LangGraph provides the production-grade foundation: compiled typed-state graphs, per-node checkpointing to Redis (via `langgraph-checkpoint-redis`), streaming, HITL interrupt/resume, and time-travel debugging. Every DeepAgents instance is a compiled LangGraph graph, meaning all LangGraph tooling (LangSmith, Studio, checkpointers) works without additional integration.

**Alternatives considered:**

- **CrewAI:** Rejected. Role-based abstraction is simpler but lacks the fine-grained control over routing, state persistence, and HITL that this system requires. CrewAI's sequential/hierarchical process model is less flexible than LangGraph's conditional edge routing. LangGraph surpassed CrewAI in GitHub stars and enterprise adoption in early 2026.

- **AutoGen (Microsoft):** Rejected. AutoGen's multi-agent conversation model does not map cleanly to a supervisor-pattern graph with typed state. Checkpointing and HITL support are less mature. Primarily designed for research rather than production deployment.

- **Custom LangGraph (without DeepAgents):** Rejected as the primary approach. Building planning, filesystem, shell, and sub-agent tooling from scratch duplicates DeepAgents' MIT-licensed work. Custom components reserved for cases where DeepAgents defaults are insufficient.

- **LangChain AgentExecutor (legacy):** Rejected. Superseded by LangGraph; lacks checkpointing, streaming, and HITL.

The deciding factor: DeepAgents returns a compiled LangGraph graph — it is not a separate framework but a configuration layer on top of LangGraph. Switching from DeepAgents to raw LangGraph for any individual agent is a small change, not a migration.

## Consequences

### Positive
- Planning, filesystem access, sub-agent delegation, and context management work out of the box — no custom implementation required
- Full LangGraph ecosystem compatibility: LangSmith tracing, Studio debugging, Redis checkpointing, streaming
- MCP support via `langchain-mcp-adapters` without additional integration code
- Provider-agnostic: any model accessible via LangChain's `init_chat_model` works, including self-hosted vLLM with OpenAI-compatible API
- MIT licensed — no licensing risk for enterprise deployment
- Active development: 9,300+ GitHub stars, 66 contributors, 615 commits as of May 2026

### Negative
- Python-only (no JS/TS agent runtime without the separate deepagents.js repository)
- Dependency on LangChain's release cadence — breaking changes in LangChain affect all agents simultaneously
- DeepAgents is an opinionated harness; customising beyond its defaults requires understanding LangGraph internals

### Neutral / Risks
- DeepAgents is deployed at v0.6.2. The 0.5.x → 0.6.x upgrade introduced `FilesystemBackend`, `SummarizationMiddleware`, `skills`, `AsyncSubAgent`, and `FilesystemPermission` — all of which are used in production. Continue to monitor for breaking changes between minor versions; pin in `pyproject.toml` with `deepagents>=0.6.1`.
- The "trust the LLM" security model of DeepAgents means agent capability is bounded by tool availability, not by model self-policing. Boundary enforcement is at the tool and network level — this is the correct model, but requires discipline in tool provisioning.

## Related Decisions
- Supersedes: (none)
- Superseded by: (none)
- Related: [ADR-0003](0003-use-multi-lora-vllm-serving-strategy.md), [ADR-0005](0005-use-mcp-for-all-tool-integrations.md), [ADR-0006](0006-self-host-langsmith-for-observability.md)
