# ADR 0005: Use MCP for All Tool Integrations

> ⚠️ **INFERRED:** This ADR was inferred from the system plan. Verify Context and Consequences before changing status to Accepted.

**Date:** 2026-05-12  
**Status:** Proposed  
**Deciders:** <TODO: names or roles>

## Context

Each agent requires access to a set of external tools: version control (GitHub/GitLab), issue tracking (Jira), code quality (SonarQube), CI/CD (Jenkins), container orchestration (Kubernetes), communication (Slack), and documentation lookup (Context7). Without a standardised integration approach, each tool requires a bespoke LangChain tool implementation with custom authentication, error handling, and schema definitions.

The system plan calls for using Red Hat's ecosystem of containerised MCP server images (220+ available via catalog.redhat.com), which provide standardised tool interfaces built on Red Hat Universal Base Images.

Constraints:
- Tool integrations must be addable without modifying agent code
- Credentials must never appear in agent context windows
- Tool access must be auditable (every tool call logged)
- New tools must be addable to an agent without redeploying the agent container

## Decision

We will use the **Model Context Protocol (MCP)** as the standard integration layer for all external tool interactions. All agent-to-external-system communication routes through MCP server containers deployed within the cluster, integrated into agents via `langchain-mcp-adapters`.

## Rationale

MCP provides a standardised protocol for connecting AI agents to external tools with well-defined schemas, error contracts, and authentication patterns. The key advantage over bespoke LangChain tool implementations is standardisation: an MCP server for a given tool (GitHub, Jira, SonarQube) defines the tool schema once; any agent can use it without custom code.

`langchain-mcp-adapters` (from LangChain) translates MCP tool definitions into standard LangChain tools at runtime. This means adding a new MCP server to an agent is a configuration change (adding the server to the agent's MCP config at boot), not a code change.

Red Hat provides UBI-based MCP server containers for 220+ tools via the Red Hat Ecosystem Catalog. Using pre-built, enterprise-supported containers reduces implementation time and ensures the MCP server containers are built on a hardened base image.

**Alternatives considered:**

- **Bespoke LangChain tool implementations per service:** Rejected. Each integration requires custom schema definitions, auth handling, error handling, and pagination. Maintenance burden scales with the number of integrations. No standardisation of tool shape across services.

- **LangChain community tools (e.g., `langchain-community` GitHub, Jira integrations):** Rejected as primary approach. Community tools vary in quality, authentication support, and schema definition. They cannot be added to an agent without a code change and package release. MCP is preferred for new integrations.

- **Direct API calls in agent code:** Rejected. Agent code calling external APIs directly means credentials must be available in the agent's environment, increasing the attack surface. MCP server containers consume credentials via Kubernetes Secrets and expose only the tool interface to agents.

## Consequences

### Positive
- Standardised tool schema across all integrations — agents learn one pattern for all tools
- New tools addable by deploying an MCP server container and updating the agent's MCP config — no agent code change required
- Credential isolation: MCP server containers consume API credentials; agents see only tool interfaces
- Red Hat UBI-based containers: hardened base image, enterprise support
- Every MCP tool call is a discrete, loggable event captured in LangSmith traces — full audit trail of external system interactions
- Tools can be versioned independently of agent code — upgrade a tool's MCP server without touching the agent

### Negative
- MCP server containers add per-agent deployment overhead: each agent namespace needs its relevant MCP servers running
- MCP protocol adds a network hop between agent and external system — small latency overhead per tool call
- MCP server quality varies across the 220+ Red Hat catalog entries; some servers may have incomplete tool coverage or bugs. Evaluate each server before adopting.
- `langchain-mcp-adapters` adds a dependency on LangChain's MCP integration layer — monitor for breaking changes

### Neutral / Risks
- MCP is a relatively young protocol (launched April 2025 in production form). The protocol itself has stabilised at v1.x, but individual MCP server implementations vary in maturity.
- Context7 MCP (Upstash) sends library name queries to an external service. This is the only MCP integration with potential data residency implications. Evaluate whether query terms are considered sensitive before production launch.

## Related Decisions
- Supersedes: (none)
- Superseded by: (none)
- Related: [ADR-0002](0002-adopt-deepagents-langgraph-for-agent-orchestration.md)
