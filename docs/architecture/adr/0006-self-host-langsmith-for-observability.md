# ADR 0006: Self-Host LangSmith for Agent Observability

> ⚠️ **INFERRED:** This ADR was inferred from the system plan. Verify Context and Consequences before changing status to Accepted.

**Date:** 2026-05-12  
**Status:** Proposed  
**Deciders:** <TODO: names or roles>

## Context

Observability for a multi-agent system is qualitatively different from observability for a traditional application. Standard APM tools (Datadog, Prometheus, Grafana) capture request rates, error rates, and latency but cannot capture the content of LLM calls, the tool invocations an agent made, the sub-agents it spawned, or the reasoning that connected steps. Without agent-native observability, debugging production failures requires manually inspecting agent logs — an impractical approach at the depth of a 12-agent system.

The system's agents are built on LangGraph (see [ADR-0002](0002-adopt-deepagents-langgraph-for-agent-orchestration.md)). LangSmith is LangChain's purpose-built observability platform for LangChain and LangGraph workloads, providing native trace capture without per-agent instrumentation.

Constraints:
- Agent execution traces contain code snippets, task descriptions, and potentially sensitive business logic — traces must not be transmitted to third-party cloud services
- Data residency requirements mandate that trace data remains on-premises
- The observability platform must capture traces from all twelve agents without per-agent integration work
- The evaluation framework must enable automated quality regression detection as LoRA adapters are trained and deployed

## Decision

We will self-host **LangSmith** (Enterprise license) within the OpenShift AI cluster. All agents will emit traces to the self-hosted LangSmith endpoint, which retains all trace data within the cluster boundary.

## Rationale

LangSmith is the only observability platform with native LangGraph trace support — it understands the graph execution model, sub-agent delegation, thread continuity across sessions, and the evaluation dataset / eval runner pattern. Custom OpenTelemetry instrumentation could capture span-level traces but would require significant engineering effort to replicate LangSmith's agent-specific features (thread view, evaluation datasets, human feedback on runs).

The self-hosted deployment option satisfies the data residency constraint while providing identical functionality to the managed cloud offering. LangSmith Enterprise includes self-hosted deployment support (Docker Compose or Kubernetes) under an enterprise license.

**Alternatives considered:**

- **LangSmith Cloud (managed):** Rejected at the constraints level — trace data would be transmitted to LangChain's managed service outside the cluster boundary.

- **Langfuse (open-source, self-hostable):** Evaluated. Langfuse supports OpenTelemetry and provides trace capture for LangChain workloads. Rejected as primary tool because: LangGraph-native trace rendering (sub-agent delegation graph, thread continuity) is more mature in LangSmith; Langfuse's evaluation dataset and eval runner features are less developed than LangSmith's as of May 2026. Langfuse remains a viable fallback if LangSmith Enterprise licensing is not approved.

- **OpenTelemetry + Jaeger / Grafana Tempo:** Evaluated. Provides distributed tracing but not agent-native views. LangSmith added OTel support in March 2025, so OTel integration is possible as a complementary export. Rejected as the primary observability tool: span-level traces without agent-semantic views (which agent called which sub-agent, what the LLM was reasoning about) are insufficient for debugging agent failures.

- **No structured observability (logs only):** Rejected. A 12-agent system with sub-agent delegation and LLM calls at every step is not debuggable from stdout logs alone. The investment in structured observability is justified by the operational risk of running agents without it.

## Consequences

### Positive
- Zero per-agent instrumentation required: LangGraph's LangSmith integration is enabled by setting `LANGCHAIN_TRACING_V2=true` at pod start — all agents emit traces automatically
- Full execution tree captured: every LLM call, tool invocation, sub-agent delegation, and state transition
- Thread continuity connects multi-turn traces across task sessions
- Evaluation datasets and automated evals enable quality regression detection as LoRA adapters are trained
- LangSmith `run_id` used as correlation field across logs, git commits, and Slack notifications — full traceability
- Trace data remains entirely within the cluster boundary

### Negative
- LangSmith Enterprise license adds cost
- Self-hosted deployment requires operational maintenance (upgrades, backup, storage management)
- LangSmith's self-hosted deployment documentation is less comprehensive than its managed cloud docs — some operational procedures require consulting LangChain support
- Storage requirement for trace archives must be planned: high-throughput agent workloads generate significant trace volume; archive policy must be defined

### Neutral / Risks
- LangSmith is a closed-source platform despite being tightly integrated with the open-source LangChain ecosystem. A future pricing or licensing change could increase cost or force migration to an alternative. Mitigated by: OTel export is now supported (March 2025) — traces can be simultaneously forwarded to an open-source backend as an insurance policy.
- Self-hosted LangSmith availability becomes a dependency for agent observability. An LangSmith outage does not block agent execution (traces are buffered and forwarded asynchronously) but creates an observability gap. Monitor LangSmith ingestion lag; alert on lag > 60 seconds.

## Related Decisions
- Supersedes: (none)
- Superseded by: (none)
- Related: [ADR-0002](0002-adopt-deepagents-langgraph-for-agent-orchestration.md)
