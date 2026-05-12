# Agentic Development Team — System Plan

**Version:** 1.0  
**Date:** May 2026  
**Status:** Planning / Pre-Architecture  
**Stack:** LangChain DeepAgents · LangGraph · LangSmith · vLLM · RedHat OpenShift AI · MCP · uv

---

## 1. Executive Summary

This document defines the full system plan for an autonomous, multi-agent software development team. The system is built on LangChain's **DeepAgents** harness (v0.4.x), orchestrated via **LangGraph**, observed through **LangSmith**, and deployed on **Red Hat OpenShift AI** with **vLLM** as the inference layer.

The team is capable of:

- Writing production-quality code across Go, TypeScript, JavaScript, Java, and Python
- Writing and running tests in strict TDD practice
- Full Git version control and workflow management (branching, PRs, merges)
- Making and documenting architectural decisions
- Managing CI/CD pipelines
- Static analysis, security scanning, and dependency management (Python managed via **uv**)
- Generating and maintaining technical documentation
- Infrastructure-as-Code and Kubernetes workload management
- Autonomous incident investigation and triage
- Proactive dependency hygiene and vulnerability patching

All agents are **skills-enabled**: capabilities are defined in a separate skills repository, tagged per agent, and loaded at runtime — enabling rolling out new skills to specific agents without redeployment.

---

## 2. Architecture Overview

### 2.1 Foundational Framework: LangChain DeepAgents + LangGraph

**DeepAgents** (`pip install deepagents`, MIT licensed, v0.4.2 stable as of Feb 2026) is the agent harness. Each agent in the system is instantiated via `create_deep_agent()`, which provides out-of-the-box:

- **Planning tools** — `write_todos` / `read_todos` for task decomposition and progress tracking
- **Filesystem access** — `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`
- **Shell execution** — `execute` for running commands in sandboxed containers
- **Sub-agent delegation** — `task` tool for spawning child agents with isolated context windows
- **Context management** — auto-summarisation when context windows fill; large outputs persisted to filesystem

`create_deep_agent()` returns a compiled **LangGraph** graph, meaning every agent natively supports:
- **Streaming** output
- **Checkpointing** — state is persisted at every transition for failure recovery
- **Human-in-the-loop** — pause graph at any node, await approval, resume
- **Time-travel debugging** — replay any historical state
- **LangSmith tracing** — full execution tree automatically captured

**MCP integration** is handled via `langchain-mcp-adapters`, allowing any MCP server to be attached to any agent as a standard tool.

### 2.2 Agent Communication Pattern

The system follows a **hierarchical supervisor pattern**:

```
User / Human-in-the-Loop
         │
         ▼
  ┌─────────────────┐
  │  Orchestrator   │  ← Master supervisor, routes all tasks
  │    Agent        │
  └────────┬────────┘
           │ delegates via `task` tool
    ┌──────┼──────┬──────────┬──────────┐
    ▼      ▼      ▼          ▼          ▼
  Code  Test   Git/VCS  Arch      CI/CD
  Agent Agent  Agent    Agent     Agent
    │      │
    └──TDD Loop──┘
           │
    ┌──────┼──────────┬──────────┐
    ▼      ▼          ▼          ▼
 Review  Security  Docs      Infra
 Agent   Agent     Agent     Agent
```

Inter-agent communication flows through **structured LangGraph state messages**. The Orchestrator maintains the master task plan. Specialist agents report back with structured results. The Orchestrator synthesises results and decides next steps.

### 2.3 Skills System

Skills live in a **dedicated Git repository** (e.g., `git.internal/dev-team/skills`). Each skill is a self-contained prompt + tool bundle tagged with one or more agent role identifiers:

```
skills/
  ├── go-expert/          # tagged: code-agent
  ├── typescript-expert/  # tagged: code-agent
  ├── tdd-protocol/       # tagged: code-agent, test-agent
  ├── adr-writer/         # tagged: arch-agent
  ├── k8s-manifest/       # tagged: infra-agent
  ├── sast-reviewer/      # tagged: security-agent
  └── pr-reviewer/        # tagged: review-agent
```

At agent boot, a **skills loader** fetches the skill repo (by tag/ref), resolves the agent's assigned skills, and injects them into the agent's system prompt and tool set. This enables:

- New skills pushed to the repo are available at next agent restart (or hot-reload with a config watch)
- No agent container rebuild or redeployment required for skill additions
- Skills can be version-pinned per agent via Git tags
- A/B testing of skill variants by pointing an agent to a branch

---

## 3. Agent Roster

### 3.1 Orchestrator Agent

**Role:** Master coordinator. Receives all user/system requests, decomposes them into tasks using its planning tools, and delegates to specialist agents.

**Responsibilities:**
- Accepting natural-language task descriptions from human users or external triggers (Jira webhooks, GitHub events)
- Breaking work into ordered subtask graphs using `write_todos`
- Routing subtasks to the correct specialist agent via the `task` sub-agent tool
- Synthesising results from parallel agent execution
- Escalating ambiguity or risk to human-in-the-loop checkpoints
- Maintaining awareness of overall system state (open PRs, failing tests, blocked agents)
- Managing retry logic on agent failures

**Tools / MCP Servers:**
- Jira MCP — creates, updates, and reads tickets linked to work items
- GitHub/GitLab MCP — reads repo state, tracks PR status
- LangSmith API — monitors ongoing agent runs
- Slack MCP — sends status updates to engineering channels

**Skills:** orchestration-strategy, task-decomposition, risk-escalation

**Human-in-the-loop triggers:** Destructive operations (force push, production deploy, schema migration), ambiguous requirements, security-critical decisions, any task touching main/prod branches

**Model:** See Section 5.1 — Orchestrator Tier

---

### 3.2 Code Generation Agent

**Role:** The primary code writer. Writes production-quality code, always following TDD practice (writes tests before implementation).

**Responsibilities:**
- Receiving feature/bug specifications from the Orchestrator
- Writing failing tests first (in coordination with the Test Agent — see TDD loop, Section 4.1)
- Implementing code to pass the tests
- Iterating until all tests pass
- Refactoring for quality once tests pass (Red → Green → Refactor)
- Using Context7 MCP to pull up-to-date library documentation before writing code using unfamiliar or fast-evolving APIs
- Producing code in: **Go, TypeScript, JavaScript, Java, Python**
- Creating feature branches via Git Agent delegation

**Tools / MCP Servers:**
- Filesystem tools (read/write/edit/glob/grep) — built into DeepAgents
- Shell execute — for running builds, formatters, linters
- Context7 MCP — up-to-date library and framework documentation
- GitHub/GitLab MCP — branch operations, file browsing
- SonarQube MCP — run static analysis on produced code

**Skills:** go-expert, typescript-expert, javascript-expert, java-expert, python-expert, tdd-protocol, clean-code, solid-principles

**TDD Workflow:** The Code Agent writes a test stub → hands off to Test Agent to validate the test is runnable and failing → Code Agent implements → Test Agent runs and reports → loop continues until green.

**Model:** See Section 5.2 — Code Tier

---

### 3.3 Test Agent

**Role:** The TDD enforcer. Owns the test suite. Writes comprehensive tests and validates all code changes against them.

**Responsibilities:**
- Writing unit, integration, and end-to-end tests
- Running the test suite and interpreting results
- Ensuring test coverage thresholds are met (configurable, default: 80% line, 70% branch)
- Generating test data and fixtures
- Identifying missing test cases in PRs
- Benchmarking and performance test authoring
- Reporting test results in structured format back to Orchestrator and Code Agent
- Flagging flaky tests and triaging intermittent failures

**Tools / MCP Servers:**
- Filesystem + shell execute — built into DeepAgents (for running test runners)
- Context7 MCP — testing framework documentation (Jest, Go testing, JUnit, pytest, etc.)
- GitHub/GitLab MCP — reading PR diffs to target test additions

**Skills:** tdd-protocol, jest-expert, pytest-expert, go-testing-expert, junit-expert, coverage-analysis, test-data-generation

**Model:** See Section 5.2 — Code Tier (can share model with Code Agent via LoRA adapter switching)

---

### 3.4 Code Review Agent

**Role:** Autonomous PR reviewer. Reviews all code changes before merge.

**Responsibilities:**
- Reviewing pull requests for correctness, readability, and maintainability
- Checking against coding standards and team conventions (loaded from skills)
- Verifying tests exist and are adequate for changed code
- Checking for common anti-patterns and code smells
- Calling SonarQube MCP to retrieve static analysis results for the PR
- Providing structured, actionable review comments via GitHub/GitLab MCP
- Approving PRs that meet all criteria or requesting changes with specific guidance
- Blocking merges that introduce critical issues

**Tools / MCP Servers:**
- GitHub/GitLab MCP — PR read, comment, review, approve/request-changes
- SonarQube MCP — static analysis results, hotspot review, code duplication
- Context7 MCP — language/framework best practice lookups
- Filesystem tools — for deeper code reading

**Skills:** pr-reviewer, sast-reviewer, go-code-standards, typescript-code-standards, java-code-standards, python-code-standards

**Model:** See Section 5.1 — Orchestrator Tier (reasoning-class model better for holistic review)

---

### 3.5 Git / VCS Agent

**Role:** Git operations specialist. Owns all version control interactions.

**Responsibilities:**
- Creating and naming feature branches following team conventions (e.g., `feat/JIRA-123-add-user-auth`)
- Staging, committing with conventional commit messages
- Pushing branches and creating pull requests with descriptive summaries
- Handling merge conflicts (attempting auto-resolution, escalating ambiguous cases)
- Rebasing branches onto main
- Tagging releases (semantic versioning)
- Managing `.gitignore`, `.gitattributes`, and submodule configurations
- Syncing fork relationships
- Archiving stale branches

**Tools / MCP Servers:**
- GitHub MCP Server — full GitHub API access (repos, branches, PRs, issues, releases)
- GitLab MCP Server — GitLab equivalent
- Shell execute — for git CLI operations beyond MCP scope
- Jira MCP — links commits/PRs to Jira tickets

**Skills:** git-conventions, conventional-commits, branching-strategy, release-tagging, conflict-resolution

**Model:** See Section 5.3 — Utility Tier (primarily deterministic tool use, lighter model sufficient)

---

### 3.6 Architecture Agent

**Role:** Technical architect. Makes and records architectural decisions.

**Responsibilities:**
- Evaluating technical options for new features and systems
- Writing Architecture Decision Records (ADRs) in the agreed format
- Reviewing proposed designs for adherence to system architecture
- Identifying architectural risks and trade-offs
- Recommending patterns (event-driven, CQRS, hexagonal architecture, etc.)
- Maintaining a living architecture document
- Flagging when implementation diverges from documented architecture
- Consulting Context7 for up-to-date framework and library capabilities before recommending them

**Tools / MCP Servers:**
- Filesystem tools — reading/writing architecture docs
- Context7 MCP — up-to-date library/framework documentation for evaluation
- GitHub/GitLab MCP — browsing existing codebase for context
- Jira MCP — linking ADRs to relevant epics/features

**Skills:** adr-writer, c4-diagrams, system-design-principles, api-design, database-design, microservices-patterns, event-driven-patterns

**Human-in-the-loop:** Architecture decisions that significantly change the system boundary, technology selection, or data model require human approval before implementation proceeds.

**Model:** See Section 5.1 — Orchestrator Tier (deep reasoning required)

---

### 3.7 CI/CD Agent

**Role:** Pipeline engineer. Owns all continuous integration and deployment automation.

**Responsibilities:**
- Writing and maintaining pipeline definitions (GitHub Actions, Jenkins, Tekton)
- Triggering builds and monitoring their progress
- Interpreting build/test failures and routing to appropriate agents
- Managing deployment manifests (Helm charts, Kustomize overlays)
- Coordinating staged rollouts (canary, blue/green)
- Rolling back failed deployments
- Managing environment-specific configurations (dev, staging, prod)
- Setting up and maintaining pipeline caching for build efficiency
- Configuring quality gates (SonarQube thresholds, test coverage requirements)

**Tools / MCP Servers:**
- Jenkins MCP Server — trigger builds, read pipeline status, manage jobs
- GitHub Actions — via GitHub MCP
- Kubernetes MCP Server — deploy workloads, check rollout status
- SonarQube MCP — configure and check quality gates
- Filesystem tools — writing pipeline YAML/Groovy definitions

**Skills:** github-actions-expert, jenkins-expert, tekton-pipelines, helm-charts, kustomize, kubernetes-deployments, canary-rollout, rollback-strategy

**Human-in-the-loop:** All production deployments require human approval. Rollbacks to production can be autonomous.

**Model:** See Section 5.3 — Utility Tier

---

### 3.8 Security Agent

**Role:** Security gatekeeper. Operates as both a guardrail and a proactive security reviewer.

**Responsibilities:**
- Screening all code before it enters the review pipeline for hardcoded secrets, credentials, and PII
- Running Software Composition Analysis (SCA) to identify vulnerable dependencies
- Static Application Security Testing (SAST) via SonarQube MCP
- Reviewing authentication and authorisation implementations
- Checking API endpoints for OWASP Top 10 vulnerabilities
- Flagging prompt injection risks in any AI-facing code the team writes
- Generating security findings reports linked to Jira tickets
- Advising on encryption, secrets management, and secure coding patterns
- Blocking CI/CD pipeline if critical security issues are found

**Tools / MCP Servers:**
- SonarQube MCP — SAST, SCA, hotspot review, security rules enforcement
- GitHub/GitLab MCP — PR blocking, security advisory integration
- Jira MCP — creating security-specific tickets
- Shell execute — running additional security tools (Trivy, Semgrep via container)

**Skills:** owasp-top-10, secrets-detection, sca-analysis, sast-review, secure-api-design, crypto-standards, jwt-security

**Input guardrail role:** The Security Agent also runs as a LangGraph node that intercepts Orchestrator outputs before they reach tool execution. It screens for prompt injection attempts, disallowed operations, and out-of-scope actions. This is distinct from its code-review role.

**Model:** See Section 5.4 — Safety/Guardrail Tier

---

### 3.9 Documentation Agent

**Role:** Technical writer. Keeps documentation in sync with code.

**Responsibilities:**
- Writing and updating README files
- Generating API documentation from code (OpenAPI, GoDoc, TypeDoc, Javadoc, pydoc)
- Writing architectural overview documentation
- Maintaining changelogs (following Keep a Changelog convention)
- Writing runbooks and operational playbooks
- Creating onboarding documentation for new engineers
- Summarising PRs and releases in human-readable form
- Translating Architecture Agent ADRs into team-facing narratives

**Tools / MCP Servers:**
- Filesystem tools — read/write docs
- GitHub/GitLab MCP — reading code for documentation derivation, writing docs PRs
- Context7 MCP — ensuring documentation examples use current API signatures
- Jira MCP — linking docs updates to feature tickets

**Skills:** technical-writing, openapi-spec, changelog-writer, runbook-writer, readme-writer

**Model:** See Section 5.3 — Utility Tier

---

### 3.10 Infrastructure Agent

**Role:** Platform engineer. Manages the Kubernetes/OpenShift environment the team's software runs in.

**Responsibilities:**
- Writing and maintaining Kubernetes manifests (Deployments, Services, ConfigMaps, Secrets)
- Managing Helm chart templates and values files
- Creating and managing OpenShift resources (Routes, BuildConfigs, ImageStreams)
- Scaling workloads based on load signals
- Managing resource quotas and limits
- Implementing network policies and pod security policies
- Setting up horizontal pod autoscaling and KEDA event-driven scaling
- Rotating secrets and certificates

**Tools / MCP Servers:**
- Kubernetes MCP Server — full CRUD on cluster resources, Helm chart installation
- Shell execute — for kubectl and helm CLI when MCP is insufficient
- Filesystem tools — reading/writing manifest files
- GitHub/GitLab MCP — pushing infrastructure changes to the GitOps repo

**Skills:** kubernetes-expert, helm-expert, openshift-expert, gitops-argocd, network-policies, hpa-keda, secrets-management

**Human-in-the-loop:** Any changes to production cluster configuration require approval. Staging changes can proceed autonomously.

**Model:** See Section 5.3 — Utility Tier

---

### 3.11 Dependency Management Agent

**Role:** Proactive dependency hygienist.

**Responsibilities:**
- Monitoring dependency versions across all repos (daily scheduled run)
- Identifying outdated packages and available upgrades
- Checking upgrade compatibility and breaking change risk
- Creating automated PRs for safe patch and minor upgrades
- Flagging major upgrades for human decision and Architecture Agent review
- Monitoring CVE feeds and prioritising security-motivated upgrades
- Detecting duplicate dependencies and recommending consolidation

**Tools / MCP Servers:**
- GitHub/GitLab MCP — creating dependency upgrade PRs
- SonarQube MCP — SCA vulnerability data
- Shell execute — running `go mod tidy`, `npm audit`, `uv lock --upgrade`, `uv run pip-audit`, `mvn versions:display-dependency-updates`
- Jira MCP — tracking dependency upgrade epics

**Skills:** dependency-management, npm-expert, go-modules-expert, maven-expert, uv-expert, semantic-versioning

**Model:** See Section 5.3 — Utility Tier

---

### 3.12 Incident Response Agent

**Role:** On-call first responder for production issues.

**Responsibilities:**
- Responding to alerting system triggers (PagerDuty, Prometheus, OpenShift monitoring)
- Reading application logs to identify root cause
- Correlating errors with recent deployments or config changes
- Proposing and (with human approval) executing remediations
- Rolling back deployments if a clear causal link is established
- Filing incident post-mortems linking findings to Jira
- Escalating to human engineers when root cause is unclear

**Tools / MCP Servers:**
- Kubernetes MCP — reading pod logs, events, resource status
- GitHub/GitLab MCP — checking recent commit history for causation
- Jira MCP — filing incident tickets and post-mortems
- Shell execute — running diagnostic commands in-cluster

**Skills:** incident-response, log-analysis, kubernetes-debugging, rollback-strategy, post-mortem-writing

**Human-in-the-loop:** All production remediations require human approval. Diagnostic reads are autonomous.

**Model:** See Section 5.1 — Orchestrator Tier (complex reasoning under pressure)

---

## 4. Inter-Agent Workflows

### 4.1 TDD Feature Development Loop

```
Orchestrator receives feature request (from Jira/user)
    │
    ├── Git Agent: creates feature branch
    │
    ├── Architecture Agent: reviews spec, confirms design, writes ADR if needed
    │       [Human checkpoint if major arch change]
    │
    ├── Code Agent: writes failing test stubs
    │
    ├── Test Agent: validates tests are runnable and failing (Red)
    │
    ├── Code Agent: implements minimum code to pass tests (Green)
    │
    ├── Test Agent: runs full suite, reports pass/fail
    │       [Loop back to Code Agent if failing]
    │
    ├── Code Agent: refactors for quality (Refactor)
    │
    ├── Test Agent: verifies refactor doesn't break tests
    │
    ├── Security Agent: scans the diff for vulnerabilities
    │
    ├── Code Review Agent: reviews PR, leaves comments
    │       [Code Agent addresses comments, loop until approved]
    │
    ├── Documentation Agent: updates relevant docs and changelog
    │
    ├── Git Agent: merges PR (squash merge by default)
    │
    ├── CI/CD Agent: monitors pipeline, verifies deployment to staging
    │       [Human checkpoint before production]
    │
    └── Orchestrator: marks Jira ticket Done, reports to Slack
```

### 4.2 Bug Fix Workflow

```
Orchestrator receives bug report (from Jira, Slack, or Incident Agent)
    │
    ├── Code Review Agent: reproduces bug, identifies affected code
    │
    ├── Test Agent: writes a failing regression test (proves the bug)
    │
    ├── Code Agent: fixes the bug (test must now pass)
    │
    ├── Security Agent: checks if bug is security-relevant (CVE filing needed?)
    │
    ├── [Standard review → merge → deploy flow as above]
    │
    └── Incident Agent: updates post-mortem if bug caused an incident
```

### 4.3 Architectural Decision Workflow

```
Orchestrator identifies need for architectural decision
    │
    ├── Architecture Agent: researches options using Context7 + filesystem
    │
    ├── Architecture Agent: writes draft ADR with options, pros/cons, recommendation
    │
    ├── Human-in-the-Loop: reviews ADR [REQUIRED]
    │
    ├── [If approved] Architecture Agent: finalises ADR, commits to repo
    │
    ├── Documentation Agent: propagates decision to relevant docs
    │
    └── Orchestrator: proceeds with implementation using decided approach
```

### 4.4 Dependency Upgrade Workflow

```
Dependency Agent: (scheduled daily)
    │
    ├── Scans all repos for outdated/vulnerable deps
    │
    ├── For each upgrade candidate:
    │       ├── Patch/minor: creates PR autonomously
    │       ├── Security CVE: creates urgent PR, alerts Slack, files Jira
    │       └── Major: creates RFC Jira ticket, assigns to Architecture Agent
    │
    ├── Test Agent: runs tests against upgrade PR
    │
    └── [Standard review → merge flow]
```

---

## 5. Model Selection Strategy

### 5.1 Orchestrator Tier — Reasoning & Decision-Making

**Recommended Model:** `Qwen/Qwen3.5-72B-Instruct` (or `Qwen3.5-32B-Instruct` for GPU budget constraints)

**Why:** The Orchestrator, Architecture Agent, Code Review Agent, and Incident Response Agent require deep reasoning, long-context understanding, and nuanced judgment. The Qwen3.5 family (released April–May 2026) offers industry-leading open-source reasoning at 72B parameters with MoE efficiency (active parameters fraction reduces compute cost). Qwen3.5-72B scores at the top of open-source benchmarks for multi-step reasoning and instruction following.

**Alternative:** `deepseek-ai/DeepSeek-V4-Pro` — hits 80.6% SWE-bench Verified, within 0.2% of frontier closed models, MIT licensed. Heavier GPU requirement but exceptional agentic coding + reasoning combo.

**Context window:** 128K tokens — essential for Orchestrator holding full task state and Architecture Agent reading large codebases.

**vLLM config:** Serve as primary base model with no LoRA (reasoning tasks benefit from full model weights).

---

### 5.2 Code Tier — Code Generation & Testing

**Recommended Model:** `Qwen/Qwen2.5-Coder-32B-Instruct`

**Why:** Qwen2.5-Coder-32B is the current open-source leader for code-specific tasks. It:
- Supports 92 programming languages including all five target languages (Go, TypeScript, JS, Java, Python)
- Achieves top open-source scores on HumanEval, MBPP, and SWE-bench Lite
- Has a 128K context window for large file reading
- Is fully vLLM compatible
- Is small enough (32B) to serve efficiently on OpenShift AI with A100/H100 GPUs

**LoRA Adapter Strategy:** Rather than serving separate models per language, serve Qwen2.5-Coder-32B as the base and attach LoRA adapters per specialisation. vLLM's multi-LoRA serving supports dynamic adapter switching at inference time with minimal overhead.

Planned LoRA adapters (trained on internal codebase after launch):
- `lora-go-internal` — Go patterns, internal library conventions
- `lora-typescript-internal` — TypeScript patterns, internal framework usage
- `lora-java-internal` — Java patterns, Spring Boot conventions
- `lora-test-expert` — test-first, coverage maximisation

At inference time the router (`langchain-mcp-adapters` skill tag → agent → LoRA tag) tells vLLM which adapter to load. vLLM hot-swaps adapters per request.

**Alternative for cost optimisation:** `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` (16B active params from 236B MoE) — excellent code quality at lower active parameter count.

---

### 5.3 Utility Tier — Deterministic Tool-Use Agents

**Recommended Model:** `Qwen/Qwen2.5-14B-Instruct`

**Why:** Git Agent, CI/CD Agent, Documentation Agent, Infrastructure Agent, and Dependency Agent primarily perform structured tool calls rather than complex reasoning. A 14B instruction-tuned model is sufficient for following deterministic workflows, producing structured outputs (YAML, JSON, Markdown), and calling MCP tools. This significantly reduces GPU resource usage for high-frequency operations.

**Alternative:** `mistralai/Mistral-Small-24B-Instruct-2501` — strong instruction following at moderate size.

**vLLM config:** Can share a single vLLM instance with the Code Tier model using vLLM's multi-model endpoint feature, or run as a separate lightweight deployment.

---

### 5.4 Safety / Guardrail Tier

**Recommended Model:** `meta-llama/Llama-Guard-3-8B`

**Why:** Llama Guard 3 is purpose-built for content and safety classification. It operates as the security screening layer in the pipeline — evaluating both inputs (from users/external triggers) and outputs (before tool execution or code merge). It is very lightweight (8B) and can run on CPU or a small GPU allocation.

**Role in pipeline:**
- Input guardrail: classifies incoming requests for prompt injection, out-of-scope instructions, or policy violations before reaching the Orchestrator
- Output guardrail: checks agent outputs for unintended data exposure, disallowed shell commands, or secret leakage before tools execute

This model runs as a separate inference endpoint (dedicated small GPU or quantised on CPU).

---

### 5.5 vLLM Serving Architecture on OpenShift AI

```
OpenShift AI Cluster
│
├── vLLM Endpoint A — "Reasoning" (Qwen3.5-72B, 2× A100 80GB, tensor parallel)
│       └── No LoRA (full precision reasoning)
│
├── vLLM Endpoint B — "Code" (Qwen2.5-Coder-32B, 1× A100 80GB)
│       └── Multi-LoRA: lora-go, lora-ts, lora-java, lora-test (hot-swappable)
│
├── vLLM Endpoint C — "Utility" (Qwen2.5-14B, 1× A100 40GB)
│       └── No LoRA (general instruction following)
│
└── vLLM Endpoint D — "Guardrail" (Llama-Guard-3-8B, CPU or T4 GPU)
        └── Safety classification only
```

**Key vLLM features in use:**
- `--enable-lora` and `--max-lora-rank` for multi-LoRA serving on Endpoint B
- `--max-num-seqs` tuned for concurrent agent requests
- OpenAI-compatible API — all LangChain model integrations use `init_chat_model("openai:...", base_url="...")`
- Quantisation: AWQ or GPTQ for Utility Tier to reduce VRAM footprint
- Prefix caching for agent system prompts (agents repeat the same prompt prefix → high cache-hit rate → major latency reduction)

**OpenShift AI integration:**
- Models served as **KServe InferenceService** resources on OpenShift AI
- Model weights stored in **OpenShift Data Foundation** (ODF/Ceph) object storage
- vLLM runtime containers from Red Hat's certified UBI base images
- Horizontal scaling via **KEDA** on request queue depth
- LoRA adapter files stored in ODF, loaded dynamically by vLLM

---

## 6. MCP Server Integrations

All MCP servers run as Red Hat UBI-based containers (pulled from `quay.io/mcp-servers/`) as per the Red Hat Ecosystem Catalog (220+ available servers). Each agent only receives the MCP tools it needs (principle of least privilege).

| MCP Server | Agents Using It | Key Capabilities |
|---|---|---|
| **GitHub MCP** | Orchestrator, Git, Code Review, CI/CD, Security, Docs, Dependency | PRs, issues, branches, releases, code browsing |
| **GitLab MCP** | Git, CI/CD | GitLab API parity with GitHub MCP |
| **Jira MCP** (`redhat-ai-tools/jira-mcp`) | Orchestrator, Security, Arch, Dependency, Incident | Tickets, sprints, linking, status updates |
| **SonarQube MCP** (`SonarSource/sonarqube-mcp-server`) | Code Review, Security, CI/CD, Dependency | SAST, SCA, quality gates, hotspots, code duplication |
| **Jenkins MCP** (Jenkins MCP Server Plugin) | CI/CD | Trigger builds, read pipeline state, manage jobs |
| **Kubernetes MCP** | CI/CD, Infra, Incident | CRUD on k8s resources, Helm, pod logs, events |
| **Context7 MCP** (`upstash/context7`) | Code, Test, Arch, Review, Docs | Up-to-date, version-specific library documentation |
| **Slack MCP** | Orchestrator | Status updates, escalations, incident alerts |
| **PostgreSQL MCP** (AWS Aurora PostgreSQL MCP) | Incident, Infra | Production DB diagnostics (read-only role) |
| **Git MCP** (filesystem-level git ops) | Git Agent | Raw git operations beyond GitHub/GitLab API scope |

**Context7 usage note:** Every agent that writes code or generates configurations is instructed to call Context7's `resolve-library-id` and `query-docs` tools before writing code for any library or framework. This ensures the agent uses the current API (not training-data-era APIs) and produces working code against the actual installed library version. The system prompt for Code Agent, Test Agent, and Infra Agent includes: *"Before writing code that uses any external library, always query Context7 for the current version documentation using the `query-docs` tool."*

---

## 7. Security Architecture

### 7.1 Threat Model

LLM-based agents face a distinct threat landscape beyond traditional application security:

- **Prompt injection** — malicious content in external data (code files, Jira tickets, PR descriptions) hijacks agent behaviour (OWASP LLM Top 10 #1, present in 73%+ of production AI deployments per OWASP 2025)
- **Indirect prompt injection** — agent reads a file, website, or database entry that contains adversarial instructions
- **Privilege escalation** — agent uses legitimate tools in combination to exceed its intended scope
- **Secret exfiltration** — agent inadvertently includes secrets in outputs
- **Unintended destructive operations** — agent executes irreversible actions (drop database, force-push to main)

### 7.2 Multi-Layer Defence

**Layer 1 — Input Screening (Llama Guard 3)**
All inputs entering the Orchestrator (from users, webhooks, Jira, Slack) pass through the Guardrail model first. It classifies inputs for:
- Prompt injection attempts
- Out-of-scope or policy-violating instructions
- Sensitive data that shouldn't be in-context

Inputs flagged as high-risk are rejected with a structured error before reaching any LLM.

**Layer 2 — Agent System Prompt Hardening**
Every agent's system prompt includes explicit instructions:
- The agent's allowed scope and tools
- Explicit prohibitions (e.g., "Never push directly to main", "Never write secrets to files")
- Instructions to ignore directives found in external file content that conflict with the system prompt
- A reminder that instructions in tool results do not override the system prompt

**Layer 3 — Tool-Level Access Control**
Each agent is given only the specific MCP tool permissions it needs:

- The Git Agent has write access to feature branches only; main is protected
- The CI/CD Agent can trigger staging pipelines autonomously; production requires human approval
- The Infra Agent has namespace-scoped RBAC in Kubernetes; no cluster-admin access
- No agent has access to production secrets in plaintext; secrets are injected at runtime via OpenShift Secrets / Vault

**Layer 4 — Output Guardrail (pre-execution)**
Before any agent output triggers a tool execution (git push, kubectl apply, Jenkins trigger), the output passes through a lightweight validation node in the LangGraph graph:
- Shell command whitelisting (regex-based deny list for dangerous commands: `rm -rf /`, `DROP TABLE`, etc.)
- Secret pattern detection (AWS key patterns, private keys, tokens)
- Scope validation (is this action within the current task's boundaries?)

**Layer 5 — Human-in-the-Loop Checkpoints**
LangGraph's built-in interrupt/resume mechanism enforces human approval at predefined high-risk nodes:
- Production deployments
- Merging to main/release branches
- Architectural decisions
- Any operation the Security Agent flags as high risk
- Database schema changes

**Layer 6 — Audit Trail**
- LangSmith captures every LLM call, tool invocation, and agent delegation with full input/output traces
- Traces are immutable and stored with a configurable retention policy
- Security-relevant events are forwarded to the organisation's SIEM
- Every git commit, PR, and deployment is attributed to the specific agent run that created it (via LangSmith run ID in commit messages)

### 7.3 Secrets Management

- Secrets never appear in agent context windows or LangSmith traces
- Environment variables injected at pod start by OpenShift Secrets / HashiCorp Vault Agent Injector
- MCP server credentials stored as Kubernetes Secrets, mounted read-only
- Agents interact with authenticated MCP servers; they never see the underlying credentials
- Regular secret rotation is managed by the Infra Agent via Vault lease management

### 7.4 Network Security

- All agents run in an isolated OpenShift namespace with restrictive NetworkPolicy
- Egress is limited to the defined MCP server endpoints and vLLM endpoints
- No agent has direct internet egress (Context7 is a deployed sidecar within the namespace)
- All agent-to-model communication is over TLS within the cluster
- Zero external ports exposed; all ingress is via the Orchestrator's controlled API

---

## 8. LangSmith Observability

### 8.1 Deployment

LangSmith is deployed **self-hosted** within the OpenShift cluster (LangSmith Enterprise license) to satisfy data residency requirements. All traces remain within the cluster boundary.

### 8.2 What is Traced

Every agent in the system is a compiled LangGraph graph and automatically emits traces to LangSmith. For each task execution, LangSmith captures:

- **Full execution tree** — every LLM call, every tool invocation, every sub-agent delegation
- **Agent reasoning** — the model's internal monologue at each step
- **Input/output pairs** — for every node in the graph
- **Token counts and latency** — per call and aggregated per task
- **Errors and retries** — with full context

### 8.3 Key Observability Dimensions

- **Per-agent dashboards** — success rate, average latency, token cost, error rate
- **Task-level traces** — full end-to-end trace from Orchestrator receipt to completion
- **TDD loop metrics** — average Red→Green cycles per feature, test coverage achieved
- **Security event feed** — guardrail trigger rate, blocked operations, escalations
- **Model comparison** — A/B evaluation as LoRA adapters are released
- **Thread continuity** — multi-turn task threads connected across sessions

### 8.4 Evaluation Framework

LangSmith's evaluation pipeline is used to continuously assess agent quality:

- **Dataset accumulation** — successful task completions (human-approved outputs) are added to evaluation datasets
- **Automated evals** — scheduled runs against eval datasets after any model or prompt change
- **Custom evaluators** — task-specific: test coverage %, code style conformance, ADR completeness score
- **Regression detection** — alert if a new LoRA adapter or skills update degrades eval scores

---

## 9. Training & Fine-tuning Strategy

### 9.1 Phase 1 — Launch with Pretrained Models

Initial system launch uses pretrained base models (Qwen2.5-Coder-32B, Qwen3.5-72B) with no fine-tuning. The skills system and prompt engineering deliver initial quality.

### 9.2 Phase 2 — Internal Codebase LoRA Adapters (6–12 weeks post-launch)

Once the system has processed enough real tasks (LangSmith provides the data), fine-tune LoRA adapters on:

- Internal coding patterns and conventions
- Internal library usage (proprietary SDKs, internal APIs)
- Team-specific commit message and PR description styles

**Training infrastructure:** Red Hat OpenShift AI with `fms-hf-tuning`; all Python training scripts managed via `uv` (open source tuning library for PyTorch FSDP). Supports expert-parallel distributed training (as of March 2026 OpenShift AI release). QLoRA (4-bit quantised LoRA) for memory efficiency during training.

**Data pipeline:**
1. LangSmith export → filter for human-approved outputs only
2. Format as instruction-tuning pairs: (task description, agent output)
3. Fine-tune LoRA adapter on Qwen2.5-Coder-32B base
4. Evaluate on held-out LangSmith eval dataset
5. If regression-free, deploy to vLLM Endpoint B

### 9.3 Phase 3 — Continuous Improvement

- Monthly LoRA refresh cycles with new high-quality examples
- Reinforcement from human feedback (RLHF) on PR review quality scores
- Architecture Agent adapter trained on approved ADR corpus
- Test Agent adapter trained on high-coverage test examples

---

## 10. Additional Capabilities (Recommended Additions)

Beyond the initial list, the following capabilities are recommended:

**10.1 Code Intelligence / Semantic Search**
A **Milvus** vector store indexed over the full codebase enables agents to semantically search for existing implementations before writing new code. This prevents duplication and ensures agents follow established patterns. The Code Agent queries this before implementing any new function.

**10.2 API Contract Management**
A dedicated sub-skill (attached to Architecture and Code Agents) manages OpenAPI/AsyncAPI specs. When the API changes, the agent updates the spec, validates backward compatibility, and triggers consumer notification.

**10.3 Performance Profiling Agent**
Triggered post-deployment: runs benchmark suites, compares against baseline, flags regressions. Useful for catching performance-impacting changes before they reach production.

**10.4 GitOps Integration**
The Infrastructure Agent operates in a GitOps model (ArgoCD). It never applies manifests directly to the cluster; instead, it commits manifest changes to the GitOps repo and ArgoCD reconciles. This provides a full audit trail and rollback capability for all infrastructure changes.

**10.5 Release Management Agent**
Automates semantic version bumps, changelog compilation, release note generation, and GitHub Release creation. Triggered when the CI/CD Agent detects a release branch is ready.

---

## 11. Architecture Handoff Notes

The following are notes for the architecture documentation phase (to be produced by the `architecture-docs` skill):

**Architecture style:** Distributed multi-agent system, event-driven coordination via LangGraph state machine, supervisor pattern with hierarchical delegation.

**Key boundaries to document in C4:**
- System context: Human users, external Git hosts, Jira, Slack, OpenShift cluster
- Container level: Each agent as a container, vLLM endpoints, MCP server containers, LangSmith, skills repo
- Component level: Within each agent — DeepAgents harness, LangGraph graph, skill loader, MCP adapter, guardrail node

**ADRs to write:**
1. Decision to use DeepAgents + LangGraph vs. CrewAI/AutoGen
2. Decision to use LoRA adapter strategy vs. separate model per agent
3. Decision to use vLLM multi-LoRA serving vs. separate inference endpoints
4. Decision to self-host LangSmith vs. managed cloud
5. Decision to use skills-as-code separate repo pattern
6. Model selection rationale for each tier

**Non-functional requirements to define:**
- Latency SLA per agent type (Orchestrator: < 30s response, Code Agent: < 5 min per feature file)
- Throughput: target concurrent task count
- Availability: HA deployment on OpenShift (3+ replicas per agent type)
- Data residency: all traces and model weights remain within cluster
- Cost constraints: GPU budget per agent tier

---

## 12. Python Package Management — uv

All Python components in this project (agent harnesses, training scripts, evaluation tooling, MCP adapters) use **[uv](https://docs.astral.sh/uv/)** as the sole Python package manager. `pip` and `virtualenv` are not used directly.

### Rationale

uv is a Rust-based Python package manager and project tool from Astral (the team behind Ruff). It is 10–100× faster than pip for dependency resolution and installation, has a fully reproducible lockfile (`uv.lock`), and replaces the need for separate tools like `virtualenv`, `pip-tools`, and `pyenv` in CI.

### Usage Across the System

**Agent containers:** Every agent is a Python project with a `pyproject.toml` and `uv.lock`. The Dockerfile for each agent uses `uv sync --frozen` to install dependencies from the lockfile — guaranteed reproducible builds.

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
CMD ["uv", "run", "python", "-m", "agent"]
```

**Skills repo:** Each skill that includes Python tooling has its own `pyproject.toml`. When the skills loader pulls a skill at runtime, it runs `uv sync` in the skill directory to ensure dependencies are present.

**CI/CD pipeline:** All pipeline steps that invoke Python use `uv run` rather than activating a virtualenv manually. The CI/CD Agent is instructed to generate pipeline steps using `uv run pytest`, `uv run ruff check`, `uv run mypy`, etc.

**Dependency Agent:** When scanning Python projects for outdated packages, the Dependency Agent runs `uv lock --upgrade` to compute the full upgrade resolution, diffs the `uv.lock` file to identify what changed, and raises a PR with the updated lockfile. For vulnerability scanning it runs `uv run pip-audit` within the project environment.

**Training scripts:** Fine-tuning and evaluation scripts use `uv` workspaces to share common dependencies (e.g., `transformers`, `datasets`, `peft`) across multiple training jobs without redundant installs.

### Key uv Commands Used by Agents

| Command | When Used |
|---|---|
| `uv sync --frozen` | Container build — install exact lockfile deps |
| `uv run <cmd>` | Run any Python tool or script in the project env |
| `uv add <package>` | Add a new dependency (Code Agent when a new lib is needed) |
| `uv lock --upgrade` | Dependency Agent — compute full upgrade resolution |
| `uv run pip-audit` | Dependency Agent — CVE scan of installed packages |
| `uv run pytest` | Test Agent — run Python test suite |
| `uv run ruff check` | Code Agent — lint Python code |
| `uv run mypy` | Code Agent — type-check Python code |
| `uv run ruff format` | Code Agent — format Python code |

### Python Version Management

uv manages Python interpreter versions via `uv python install`. The project standardises on **Python 3.12** across all agent containers and training environments. The target version is pinned in each `pyproject.toml`:

```toml
[project]
requires-python = ">=3.12"
```

---

## 13. Technology Reference

| Component | Technology | Version |
|---|---|---|
| Agent Harness | LangChain DeepAgents | 0.4.2 |
| Orchestration Graph | LangGraph | v1.x |
| MCP Integration | langchain-mcp-adapters | latest |
| Observability | LangSmith (self-hosted) | Enterprise |
| Inference Runtime | vLLM | latest stable |
| Model Platform | Red Hat OpenShift AI | 2.x |
| Orchestrator Model | Qwen3.5-72B-Instruct | Apr 2026 |
| Code Model | Qwen2.5-Coder-32B-Instruct | — |
| Utility Model | Qwen2.5-14B-Instruct | — |
| Guardrail Model | Llama-Guard-3-8B | — |
| Documentation Lookup | Context7 MCP (Upstash) | latest |
| VCS | GitHub / GitLab (via MCP) | — |
| CI Platform | Jenkins / GitHub Actions (via MCP) | — |
| Code Quality | SonarQube (via MCP) | — |
| Issue Tracking | Jira (via MCP) | — |
| Container Platform | OpenShift (Kubernetes) | 4.x |
| GitOps | ArgoCD | — |
| Secrets Management | HashiCorp Vault / OpenShift Secrets | — |
| Vector Store | Milvus | latest stable |
| State Checkpointer | Redis + langgraph-checkpoint-redis | 7.x |
| Python Package Manager | uv (Astral) | latest |
| Languages | Go, TypeScript, JavaScript, Java, Python | — |

---

*This document is the planning input for the architecture-docs skill. Next step: run the `architecture-docs` skill against the development-team workspace to generate the full C4 diagram suite, ADR templates, and stakeholder-facing architecture narrative.*
