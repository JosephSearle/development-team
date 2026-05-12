# 09 — Risks and Technical Debt

**Audience:** Architects, engineering leads

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|
| **Prompt injection via external data** — malicious content in Jira tickets, PR descriptions, or code files hijacks agent behaviour (OWASP LLM #1) | High | Critical | Six-layer defence: Llama Guard 3 input screening, system prompt hardening, tool-level scoping, output guardrail, HITL gate, and LangSmith audit trail |
| **Indirect prompt injection** — agent reads a file or URL containing adversarial instructions that override system prompt | High | High | System prompt explicitly instructs agents to ignore conflicting instructions from external data; tool output is presented as data, not instructions |
| **vLLM inference endpoint outage** — all dependent agents blocked | Medium | Critical | Minimum 2-replica inference deployments; KEDA autoscaling; vLLM health-check probe with automatic pod restart; Orchestrator marks degraded agents and suspends delegation |
| **Context window exhaustion in long tasks** — Orchestrator loses task context in multi-hour executions | Medium | High | DeepAgents auto-summarisation at configurable token threshold; large outputs persisted to filesystem and referenced by path rather than included in context |
| **LangGraph state schema drift** — incompatible state between running agents after a rolling update | Medium | High | State schema versioning; rolling updates pause until all in-flight tasks complete (or are resumed from checkpoint on new version); integration tests for schema compatibility |
| **LoRA adapter poisoning** — a malicious or miscalibrated training run produces an adapter that degrades output quality | Low | High | Adapters validated on LangSmith eval dataset before promotion to production; adapter files are checksummed in ODF; Production adapter promotion requires human approval |
| **GPU hardware failure** — loss of A100 nodes blocks inference | Low | Critical | Multi-node GPU pool; KServe restarts on different GPU nodes; Reasoning endpoint runs with tensor parallelism across two GPUs (single-node failure = full restart) |
| **Secrets exfiltration via agent output** — agent inadvertently includes injected secret in a log, commit, or Slack message | Low | Critical | Output guardrail scans for secret patterns (regex); Vault Agent Injector delivers secrets as tmpfs files (no env var leakage); LangSmith trace scrubbing for known secret patterns |
| **Cascading agent failures** — one failing agent blocks the Orchestrator's entire plan | Medium | High | Orchestrator has retry logic with exponential backoff per subtask; circuit-breaker pattern per agent type; failed subtasks trigger Slack escalation rather than silent blockage |
| **MCP server unavailability** — GitHub API rate limit or Jira outage blocks task progress | Medium | Medium | Exponential backoff retry in MCP adapter; Orchestrator queues dependent subtasks and notifies Slack; tasks resume when the tool becomes available |
| **Skills repository unavailable at agent boot** — agents start without their skill bundles | Low | Medium | Skills are fetched at boot and cached in-pod; agent falls back to base behaviour without skills rather than failing to start; alert on skills load failure |
| **LoRA adapter swap latency spike** — high-throughput Code Agent requests with frequent language switching degrade throughput | Medium | Medium | Evaluate pre-loading all adapters at vLLM start rather than dynamic loading if swap latency > 2s in production |
| **Data residency breach** — trace data accidentally forwarded to LangSmith Cloud | Low | High | `LANGCHAIN_ENDPOINT` points exclusively to self-hosted LangSmith; network policy blocks egress to LangSmith Cloud domain; startup check validates endpoint URL |

---

## Failure Mode Catalog

| Failing Component | Impact on System | Mitigation in Place |
|---|---|---|
| Orchestrator Agent pod | All new task intake blocked; in-flight tasks resume from LangGraph checkpoint on pod restart | 2 replicas; LangGraph checkpoint enables resume; KEDA restarts within seconds |
| Code Agent pods | Feature development blocked; test-writing tasks queued | 2 replicas; Orchestrator queues tasks; Slack escalation after 5-min queue depth threshold |
| vLLM Reasoning endpoint | Orchestrator, Review, Architecture, and Incident agents blocked | 2+ GPU replicas; KServe restarts pod; 99.9% availability target |
| vLLM Code endpoint | Code and Test agents blocked | Horizontal scaling; KServe restarts; highest-priority endpoint for alerting |
| LangSmith | Observability gap — agents continue functioning | Alert on trace ingestion lag > 60s; LangGraph checkpointer continues to provide state persistence independently |
| Redis Checkpointer | In-flight task state cannot be persisted; new tasks blocked | Redis Sentinel HA (1 primary + 2 replicas); automatic failover < 30s; AOF persistence enables recovery from full cluster restart; PodDisruptionBudget enforces single-pod restart |
| GitHub / GitLab MCP unavailable | Git Agent and Code Review Agent blocked | MCP retry with backoff; tasks queued; Slack alert after 10-min outage |
| Jira MCP unavailable | Orchestrator cannot read new task requirements | Queues pending; engineer can supply tasks directly via Slack; Jira MCP retry |
| Vault unavailable | Agent pods cannot start (secrets not injected) | Vault HA cluster (3 nodes); Vault Agent Injector caches credentials in pod; existing pods unaffected |

---

## Technical Debt

**Known at system inception:**

- **No integration tests for agent-to-agent message contracts.** The LangGraph state schema is tested at unit level within each agent. Cross-agent contract tests (ensuring Code Agent output is correctly parsed by Security Agent) do not yet exist. *Risk: state schema changes in one agent may silently break downstream agents.*

- **LoRA adapters are not yet trained.** The initial system launches with base Qwen2.5-Coder-32B and no language-specific LoRA adapters. Language specialisation is delivered entirely through system prompts and skills. LoRA training is planned for Phase 2 (6–12 weeks post-launch). *Risk: sub-optimal code quality in target languages until adapters are trained.*

- **No E2E performance benchmarks against real GPU hardware.** All performance targets in §07 are estimates based on published vLLM benchmarks. Real TTFT and throughput figures must be measured on the actual A100 hardware allocation before production SLAs can be committed. *Risk: SLA commitments made before hardware validation may be incorrect.*

- **Context7 MCP is externally hosted.** The system relies on Upstash-hosted Context7 for library documentation lookups. This is the only dependency that creates potential data residency ambiguity (query terms sent to external service). *Recommended: evaluate self-hosting Context7 or using a cached local documentation mirror.*

- **Skills hot-reload is not implemented.** Skills are fetched at agent boot. A new skill deployment requires an agent pod restart. Zero-downtime skill updates require a config-watch mechanism not yet designed. *Risk: skill updates have a restart window.*

- **Incident Response Agent has no direct alerting integration.** The agent is triggered by Orchestrator; it does not directly subscribe to Prometheus/PagerDuty alerts. A direct alert webhook handler would reduce mean time to agent engagement. *Planned for Phase 2.*

- **No chaos engineering tests.** The failure mode mitigations described above are designed but not validated under real failure conditions. Chaos testing (pod kill, GPU node drain, database failover) should be run in staging before production launch.
