# Agentic Development Team — Architecture Documentation

This directory contains the architecture documentation for the Agentic Development Team system: a fully autonomous, multi-agent software engineering platform built on LangChain DeepAgents, LangGraph, and Red Hat OpenShift AI.

> **Start here:** New to this system? Read [01-system-context.md](01-system-context.md) first, then [08-technology-stack.md](08-technology-stack.md), then the [ADR index](adr/) for key decision history.

---

## Section Index

| File | Description | Primary Audience |
|---|---|---|
| [01-system-context.md](01-system-context.md) | What the system does, who uses it, and how it fits in the wider world | Business stakeholders, architects |
| [02-container-architecture.md](02-container-architecture.md) | The major deployable units (agents, inference endpoints, data stores) and how they communicate | Architects, senior engineers |
| [03-component-view.md](03-component-view.md) | Internal structure of the Orchestrator Agent and Development Domain — the most architecturally significant containers | Engineers |
| [04-data-architecture.md](04-data-architecture.md) | Data stores, ownership boundaries, the LangGraph state schema, and event catalog | Engineers, architects |
| [05-deployment.md](05-deployment.md) | OpenShift AI deployment topology, environments, scaling, and CI/CD pipeline | DevOps, platform engineers |
| [06-cross-cutting-concerns.md](06-cross-cutting-concerns.md) | Security, observability, secrets management, agent guardrails, and error handling | Engineers, security engineers |
| [07-quality-and-nfrs.md](07-quality-and-nfrs.md) | Performance targets, SLAs, availability requirements, and quality goals | Architects, product owners |
| [08-technology-stack.md](08-technology-stack.md) | Full technology stack table with rationale | All engineers, new team members |
| [09-risks-and-debt.md](09-risks-and-debt.md) | Identified risks, failure modes, and known technical debt | Architects, engineering leads |
| [10-glossary.md](10-glossary.md) | Domain-specific terminology used across this system | New team members, all |
| [adr/](adr/) | Architecture Decision Records — the why behind key technical choices | Architects, engineers |
| [.checklist.md](.checklist.md) | Working document: outstanding TODOs and items requiring human input | Engineering leads |

---

## How to Keep This Documentation Current

Architecture documentation must be updated as part of the development workflow. The following changes **require** a documentation update before the associated PR is merged:

- Adding or removing an agent container
- Adding a new MCP server integration
- Changing the communication pattern between two agents
- Changing the model tier assignment for any agent
- Adding or changing a data store
- Any change to the OpenShift AI deployment topology
- Any change to a quality target or SLA in §07
- Any significant technology decision — create an ADR

**Review cadence:** Conduct a documentation review every 6 months. Verify each section still reflects reality; supersede outdated ADRs rather than editing them.

---

## ADR Quick Index

| ADR | Title | Status |
|---|---|---|
| [0001](adr/0001-record-architecture-decisions.md) | Record Architecture Decisions | Accepted |
| [0002](adr/0002-adopt-deepagents-langgraph-for-agent-orchestration.md) | Adopt DeepAgents + LangGraph for Agent Orchestration | Proposed |
| [0003](adr/0003-use-multi-lora-vllm-serving-strategy.md) | Use Multi-LoRA vLLM Serving Strategy | Proposed |
| [0004](adr/0004-host-models-on-openshift-ai.md) | Host Models on Red Hat OpenShift AI | Proposed |
| [0005](adr/0005-use-mcp-for-all-tool-integrations.md) | Use MCP for All Tool Integrations | Proposed |
| [0006](adr/0006-self-host-langsmith-for-observability.md) | Self-Host LangSmith for Agent Observability | Proposed |
