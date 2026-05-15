# 07 — Quality Attributes and Non-Functional Requirements

**Audience:** Architects, product owners  
<!-- Replace all TBD values with real, measured targets before first production deployment. "High performance" is not a target. -->

---

## Quality Goals

| Goal | Measurable Target | Priority | Rationale |
|---|---|---|---|
| Task throughput | TBD — establish baseline from staging | High | The system's primary value is removing bottlenecks; throughput must be measurable |
| Code generation latency | < 5 min from task assignment to first commit for a single-file feature | High | Latency > 10 min reduces perceived value; code agents block on LLM inference |
| Orchestrator response time | < 30 sec from task receipt to first sub-agent delegation | High | Human-facing latency; engineers expect near-interactive response |
| Test coverage threshold | ≥ 80% line coverage, ≥ 70% branch coverage on all new code | High | Enforced structurally by Test Agent before PR creation |
| Security scan pass rate | 0 Critical or High severity findings permitted to merge | Critical | Security Agent blocks PR creation on Critical/High findings |
| Agent availability | ≥ 99.5% during business hours | High | Agent pods run with ≥ 2 replicas; KEDA handles demand spikes |
| Inference endpoint availability | ≥ 99.9% (Reasoning + Code tiers) | Critical | All agents depend on inference; downtime blocks all tasks |
| LangSmith trace completeness | 100% of LLM calls and tool invocations captured | High | Required for audit, debugging, and evaluation |
| Mean Time to Recovery (MTTR) for agent failures | < 5 min (pod restart + state resume from checkpoint) | High | LangGraph checkpointing enables mid-task resume; no full restart needed |
| LoRA adapter swap latency | < 2 sec per adapter switch | Medium | Impacts throughput when Code Agent switches between language LoRA adapters |

---

## Constraints

**Technical constraints:**
- All components must run within the Red Hat OpenShift AI cluster boundary. No agent may call external APIs except through designated MCP server containers within the cluster.
- Model weights must reside in on-premises ODF/Ceph object storage. No model may be loaded from an external registry at inference time.
- Python agent components must use `uv` for dependency management and `uv sync --frozen` in all CI builds. No `pip install` or unversioned package installation is permitted.
- The guardrail model (Llama-Guard-3-8B) must intercept all inputs before any other LLM call on the critical path. This is a hard architectural constraint, not a guideline.
- Shell execution by agents must use gVisor (runsc) isolation. Unrestricted shell access is not permitted.

**Organisational constraints:**
- Production deployments require explicit human approval via the HITL gate. Fully autonomous production deployment is not a permitted configuration.
- All architectural decisions that affect system boundaries, model selection, or data residency require an ADR reviewed and accepted by the engineering lead before implementation.
- No regulatory compliance framework (GDPR, SOC2, HIPAA, etc.) has been formally scoped for this system. If the system processes personal data or is submitted for compliance certification, a dedicated compliance review and updated ADR are required before production go-live.

**Data residency constraints:**
- All LangSmith traces, LangGraph state, and codebase embeddings must remain within the cluster. No trace data may be forwarded to LangSmith Cloud.
- Model weights and LoRA adapters must reside in on-premises ODF storage.

---

## Performance Targets

<!-- Validate these targets against actual vLLM benchmarks on your GPU hardware before committing to SLAs. TBD values must be measured in staging before first production deployment. -->

| Component | Metric | Target |
|---|---|---|
| vLLM Reasoning (Qwen3.5-72B) | Time to First Token (TTFT) | TBD — measure on A100 hardware |
| vLLM Reasoning (Qwen3.5-72B) | Inter-Token Latency (ITL) | TBD |
| vLLM Code (Qwen2.5-Coder-32B) | TTFT with prefix cache hit | TBD |
| vLLM Code (Qwen2.5-Coder-32B) | LoRA adapter swap time | < 2 sec |
| vLLM Guardrail (Llama-Guard-3-8B) | End-to-end classification latency | < 500ms P95 |
| Context7 MCP | Documentation query response time | < 3 sec P95 |
| Built-in grep/glob (codebase search) | Live file search per agent task | No SLA — synchronous filesystem operation; bounded by workspace size |
| Redis checkpoint write | State persistence latency | < 10ms P95 (Redis in-memory write) |

---

## Security Baseline

The following security controls are mandatory. All are architectural constraints, not optional hardening:

- **Input guardrail active on all ingress paths.** No LLM call may execute on externally-sourced input that has not passed Llama Guard 3 classification.
- **No credentials in agent context windows.** All secrets injected via Vault Agent Injector at pod start; MCP servers consume credentials, agents do not.
- **No direct internet egress from agent pods.** All external system calls route through MCP server containers subject to network policy.
- **All production operations require HITL approval.** The LangGraph interrupt node is not bypassable by agent logic.
- **Shell execution uses gVisor isolation.** Unrestricted kernel access from agent-executed code is not permitted.
- **All agent-to-model traffic is TLS-encrypted** within the cluster.
- **LangSmith traces are stored self-hosted.** No task content, code, or credentials are transmitted outside the cluster boundary.

---

## Maintainability

- Agent skills are bundled as SKILL.md files within each agent's Python package (at `agents/<name>/src/<module>/skills/<skill-name>/SKILL.md`). DeepAgents ≥0.6.1 loads them via the `skills=` parameter at agent instantiation. Updating a skill requires a new package release and pod rollout, but no re-architecture of the agent.
- New LoRA adapters can be added to the Code endpoint by uploading to ODF and updating the vLLM KServe InferenceService manifest. No model redeployment is required; vLLM loads adapters at request time.
- LangGraph graph definitions are code — all node logic, routing rules, and HITL conditions are version-controlled and tested as part of the agent Python packages.
- Every significant architectural change must be accompanied by an ADR. See [docs/architecture/adr/](adr/).

<!-- enriched by architecture-docs skill, 2026-05-15 -->
