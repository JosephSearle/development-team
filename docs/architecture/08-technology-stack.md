# 08 — Technology Stack

**Audience:** All engineers, new team members

<!-- Version numbers reflect the plan as of May 2026. Update this table when versions are pinned in pyproject.toml / go.mod / Helm values files. -->

---

## Stack Table

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| **Agent Harness** | LangChain DeepAgents | 0.4.2 | Batteries-included agent harness built on LangGraph: planning tools, filesystem access, shell execution, sub-agent spawning, and context management out of the box. MIT licensed. See [ADR-0002](adr/0002-adopt-deepagents-langgraph-for-agent-orchestration.md) |
| **Orchestration Graph** | LangGraph | v1.x | Compiles agent logic as directed cyclic graphs with typed state, built-in checkpointing, streaming, HITL interrupt/resume, and time-travel debugging. Returns a standard compiled graph — compatible with all LangGraph tooling. See [ADR-0002](adr/0002-adopt-deepagents-langgraph-for-agent-orchestration.md) |
| **MCP Integration** | langchain-mcp-adapters | latest stable | Presents MCP server tools as standard LangChain tools; enables any MCP server to be attached to any agent without custom integration code. See [ADR-0005](adr/0005-use-mcp-for-all-tool-integrations.md) |
| **Agent Runtime** | Python | 3.12 | Supported by LangChain, DeepAgents, and the full ML tooling ecosystem. Pinned via `requires-python = ">=3.12"` in all `pyproject.toml` files. |
| **Python Package Manager** | uv (Astral) | latest stable | Replaces pip + virtualenv + pip-tools with a single Rust-based tool. 10–100× faster dependency resolution; reproducible lockfiles via `uv.lock`; `uv sync --frozen` in all CI builds. |
| **Observability** | LangSmith (self-hosted) | Enterprise | Full agent observability: traces every LLM call, tool invocation, and sub-agent delegation. Self-hosted for data residency. Threads connect multi-turn traces. Evaluation datasets and automated evals. See [ADR-0006](adr/0006-self-host-langsmith-for-observability.md) |
| **Inference Runtime** | vLLM | latest stable | OpenAI-compatible inference server; multi-LoRA adapter serving (dynamic per-request swap); prefix caching; tensor parallelism; KServe integration. See [ADR-0003](adr/0003-use-multi-lora-vllm-serving-strategy.md) |
| **Model Platform** | Red Hat OpenShift AI | 2.x | Kubernetes-native ML platform: KServe for model serving, fms-hf-tuning for LoRA fine-tuning, ODF for model storage, GPU operator for hardware management. See [ADR-0004](adr/0004-host-models-on-openshift-ai.md) |
| **Orchestrator / Architecture / Review / Incident Model** | Qwen3.5-72B-Instruct | Apr 2026 | Top open-source reasoning model; 128K context window; MoE architecture with high active-parameter efficiency. Serves the four agents requiring deep, multi-step reasoning. |
| **Code / Test Model** | Qwen2.5-Coder-32B-Instruct | — | Specialist code model; top open-source coding benchmark scores; 128K context; 92 language support including all five target languages. Base model for LoRA adapter strategy. |
| **Utility Model** | Qwen2.5-14B-Instruct | — | General-purpose instruction follower for deterministic tool-use agents (Git, CI/CD, Docs, Infra, Dependency). Efficient on A100 40GB. |
| **Guardrail Model** | Llama-Guard-3-8B | — | Purpose-built safety classifier; classifies inputs and outputs for policy violations and prompt injection. Runs on T4 GPU; P95 latency target < 500ms. |
| **Container Platform** | Red Hat OpenShift (Kubernetes) | 4.x | All agent, inference, and platform workloads run as Kubernetes workloads. NetworkPolicy for namespace isolation; RBAC for service accounts. |
| **GitOps** | ArgoCD | latest stable | Reconciles Kubernetes manifests from the GitOps repository. Infrastructure Agent commits; ArgoCD applies. No agent uses `kubectl apply` directly. |
| **Autoscaling** | KEDA | latest stable | Event-driven autoscaling for agent pods based on LangSmith queue depth metrics. |
| **Secrets Management** | HashiCorp Vault | latest stable | All credentials stored in Vault; injected at pod start via Vault Agent Injector. External Secrets Operator syncs to Kubernetes Secrets for MCP containers. |
| **Object Storage** | ODF / Ceph (S3-compatible) | — | On-premises object storage for model weights, LoRA adapter files, and LangSmith trace archives. S3-compatible API used by vLLM and LangSmith. |
| **Vector Store** | Milvus | latest stable | Purpose-built vector database for codebase semantic search. Chosen over pgvector for purpose-built ANN index performance, built-in collection management, and horizontal scalability as embedding volume grows. gRPC-native API. |
| **State Checkpointer** | Redis + langgraph-checkpoint-redis | 7.x | LangGraph checkpointer backend using Redis for in-memory state persistence. Sub-10ms write latency; Redis Sentinel for HA. `noeviction` policy protects in-flight graph state. AOF enabled for durability. |
| **CI/CD** | GitHub Actions / Jenkins | — | GitHub Actions for repositories hosted on GitHub; Jenkins for on-premises builds. Pipeline definitions written and maintained by the CI/CD Agent. |
| **Code Quality** | SonarQube | latest stable | SAST, SCA, hotspot review, and quality gate enforcement on every PR. Integrated via SonarQube MCP server. |
| **Issue Tracking** | Jira | Cloud / Server | Source of task requirements for the Orchestrator; destination for status updates, PR links, and incident post-mortems. Integrated via Jira MCP server. |
| **Documentation Lookup** | Context7 (Upstash) | latest | Up-to-date, version-specific library documentation fetched by code-writing and infrastructure agents before using any external library. Prevents stale-API-knowledge bugs. |
| **Shell Isolation** | gVisor (runsc) | latest | Sandboxes shell execution by agent containers. Provides kernel isolation without a full VM. Protects the cluster from agent-executed code that could escape the container. |
| **Target Languages** | Go, TypeScript, JavaScript, Java, Python | — | The five languages the Code Agent and Test Agent are skilled in. Each language has a corresponding LoRA adapter and skill bundle. |
| **Python Linter / Formatter** | Ruff | latest | Single tool replacing flake8, isort, and black. Invoked by Code Agent via `uv run ruff check` and `uv run ruff format`. |
| **Python Type Checker** | mypy | latest | Static type checking for Python agent code. Invoked by Code Agent via `uv run mypy`. |
| **Python Test Runner** | pytest | latest | Standard Python test runner. Invoked by Test Agent via `uv run pytest`. |
| **Database Migrations** | Alembic | latest | Manages Vector Store schema migrations. Invoked by Infrastructure Agent via `uv run alembic upgrade head` during deployment. |
