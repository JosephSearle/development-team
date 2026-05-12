# 10 — Glossary

**Audience:** New team members, all engineers

Terms are listed alphabetically. All terms are specific to this system's domain; for general Kubernetes or Python terminology, refer to upstream documentation.

---

| Term | Definition |
|---|---|
| **ADR (Architecture Decision Record)** | A short Markdown document recording a significant architectural decision: what was decided, why, and what the trade-offs are. Stored in `docs/architecture/adr/`. Accepted ADRs are immutable — supersede, never edit. |
| **Agent** | A deployable Python service built on DeepAgents that executes a specific engineering role (e.g., Code Agent, Git Agent). Each agent is a compiled LangGraph graph with its own model tier, tool set, and skill bundle. |
| **Agent Router** | The conditional edge component within the Orchestrator that determines which specialist agent handles each subtask, based on task type and dependency graph. |
| **ArgoCD** | The GitOps reconciliation controller that watches the GitOps repository and applies Kubernetes manifest changes to the cluster. The Infrastructure Agent commits; ArgoCD applies. |
| **Checkpointer** | The LangGraph persistence mechanism that writes a full snapshot of graph state to Redis at every node transition using `langgraph-checkpoint-redis`. Enables failure recovery, task resume, and time-travel debugging. |
| **Code Tier** | The inference tier serving the Code Agent and Test Agent. Uses Qwen2.5-Coder-32B-Instruct as the base model with hot-swappable LoRA adapters per language. |
| **Context7** | An MCP server (by Upstash) that retrieves up-to-date, version-specific documentation for any library or framework. Code-writing agents query Context7 before using any external API to avoid using stale training-data-era knowledge. |
| **DeepAgents** | The LangChain agent harness (`pip install deepagents`) that provides planning tools, filesystem access, shell execution, and sub-agent spawning out of the box. Every agent in this system is a DeepAgents instance. |
| **Development Domain** | The capability group comprising the Code Agent, Test Agent, and Code Review Agent. Responsible for all code writing, test writing, and PR review. |
| **Engineering Domain** | The capability group comprising the Git Agent, CI/CD Agent, Security Agent, and Infrastructure Agent. Responsible for all VCS operations, pipeline management, security scanning, and platform management. |
| **GitOps** | The practice of storing all Kubernetes infrastructure definitions in a Git repository and using a reconciliation controller (ArgoCD) to apply them. No agent applies manifests directly to the cluster. |
| **Guardrail** | A LangGraph node that intercepts agent inputs or outputs and validates them for safety, policy compliance, and secret leakage. Implemented using the Llama-Guard-3-8B model. |
| **Guardrail Tier** | The inference tier serving the Security Agent's input and output classification function. Uses Llama-Guard-3-8B on T4 GPU. |
| **HITL Gate (Human-in-the-Loop Gate)** | A LangGraph interrupt node that pauses graph execution and awaits a human approval token before proceeding. Required for all production deployments, main-branch merges, and architectural decisions. |
| **Intelligence Domain** | The capability group comprising the Architecture Agent, Documentation Agent, Dependency Agent, and Incident Response Agent. |
| **KServe InferenceService** | The Kubernetes custom resource used to deploy vLLM model-serving instances on OpenShift AI. Each vLLM tier is a separate InferenceService. |
| **KEDA** | Kubernetes Event-Driven Autoscaling. Scales agent pod replicas based on LangSmith task queue depth metrics. |
| **LangGraph** | The orchestration framework underlying all agents. Models agent logic as directed cyclic graphs with typed state, checkpointing, streaming, and HITL support. |
| **LangSmith** | The observability platform capturing all agent traces. Self-hosted within the cluster. Traces every LLM call, tool invocation, and sub-agent delegation. |
| **LoRA Adapter** | A Low-Rank Adaptation weight file that fine-tunes a base model for a specific task (e.g., Go code generation) without modifying the base model weights. vLLM swaps adapters per request at inference time. |
| **Milvus** | The purpose-built vector database used for codebase semantic search. Stores embeddings of source code chunks and supports approximate nearest-neighbour (ANN) queries via the Milvus SDK over gRPC. Deployed as a StatefulSet; uses etcd for metadata and ODF for persistent storage. |
| **MCP (Model Context Protocol)** | A standardised protocol for connecting AI agents to external tools and data sources. All external system integrations (GitHub, Jira, SonarQube, etc.) are accessed via MCP servers. |
| **MCP Server** | A containerised service that implements the MCP protocol for a specific external system. Red Hat provides UBI-based MCP server containers via the Red Hat Ecosystem Catalog. |
| **Multi-LoRA Serving** | The vLLM capability to serve multiple LoRA adapters on a single base model instance, switching adapters per request. Enables the Code Tier to serve Go, TypeScript, Java, Python, and test-specific adapters from a single 32B model deployment. |
| **ODF (OpenShift Data Foundation)** | The on-premises object storage platform (Ceph-based) used to store model weights, LoRA adapter files, and LangSmith trace archives. Provides an S3-compatible API. |
| **Orchestration Layer** | The capability group comprising the Orchestrator Agent and Skills Loader. The single entry point for all tasks; routes work to all other agents. |
| **Orchestrator Agent** | The master supervisor agent. Decomposes task requirements, routes subtasks to specialist agents, manages the HITL gate, and synthesises results. All other agents are sub-agents of the Orchestrator. |
| **Prefix Caching** | A vLLM optimisation that caches the KV-cache values for repeated prompt prefixes (e.g., agent system prompts). Significantly reduces Time to First Token for repeated calls from the same agent. |
| **Reasoning Tier** | The inference tier serving the Orchestrator, Architecture, Code Review, and Incident Response Agents. Uses Qwen3.5-72B-Instruct on 2× A100 80GB with tensor parallelism. |
| **Red-Green-Refactor** | The TDD cycle enforced by the Development Domain. Red = write a failing test; Green = write minimum code to pass; Refactor = improve code quality without changing behaviour. The LangGraph state machine enforces this as a structural constraint. |
| **run_id** | The LangSmith unique identifier for a single agent execution. Propagated as a correlation field in all logs, git commit messages, and sub-agent traces, enabling end-to-end traceability. |
| **Skills** | Self-contained bundles of system prompt extensions and tool configurations stored in the skills Git repository. Loaded by the Skills Loader at agent boot and injected into the agent's context without redeploying the agent container. |
| **Skills Loader** | The component that fetches skill bundles from the skills Git repository at agent boot, filtered by the agent's assigned role tags, and injects them into the agent's system prompt and tool set. |
| **SCA (Software Composition Analysis)** | Automated analysis of third-party dependencies for known vulnerabilities (CVEs). Performed by the Security Agent and Dependency Agent via SonarQube MCP. |
| **SAST (Static Application Security Testing)** | Automated analysis of source code for security vulnerabilities without executing the code. Performed by the Security Agent via SonarQube MCP on every PR. |
| **Sub-Agent** | A specialist agent instantiated by the Orchestrator's `task` tool with an isolated context window. Returns a structured result to the Orchestrator. Each of the 11 specialist agents can be invoked as a sub-agent. |
| **Task** | The unit of work processed by the Orchestrator. A task originates from a Jira ticket or engineer prompt, is decomposed into subtasks, executed across specialist agents, and concludes with a PR, a deployment, or a structured result. |
| **TDD (Test-Driven Development)** | The development practice of writing failing tests before writing implementation code. Enforced structurally in this system: the Code Agent cannot commit code that does not pass its corresponding tests. |
| **Tensor Parallelism** | The vLLM strategy of splitting a single model's weights across multiple GPUs. Used for the Reasoning Tier (Qwen3.5-72B) which requires 2× A100 80GB. |
| **Utility Tier** | The inference tier serving the Git, CI/CD, Documentation, Infrastructure, and Dependency Agents. Uses Qwen2.5-14B-Instruct on A100 40GB. |
| **uv** | The Rust-based Python package manager (by Astral) used for all Python components in this project. Provides reproducible builds via `uv.lock`, replaces pip + virtualenv, and is used in all CI builds via `uv sync --frozen`. |
| **vLLM** | The inference runtime serving all LLM models. Provides an OpenAI-compatible REST API, multi-LoRA support, prefix caching, and tensor parallelism. Deployed as KServe InferenceService on OpenShift AI. |
