# 01 — System Context

**Audience:** Business stakeholders, architects  
**C4 Level:** 1 — Context

---

## System Purpose

The Agentic Development Team is an autonomous, multi-agent software engineering platform. It accepts development tasks in natural language — from a human engineer, a product ticket, or an automated trigger — and carries out the full development lifecycle: writing tests, implementing code, managing version control, running CI/CD pipelines, reviewing code quality, and deploying to staging. Human engineers remain in control of architectural decisions and production deployments, with all other routine engineering work delegatable to the system.

The system is designed to operate alongside a human engineering team, not replace it. It handles the mechanical throughput of software delivery so that human engineers can focus on product direction, architectural judgment, and work requiring interpersonal context.

---

## Business Context

Software engineering teams face a persistent tension between delivery speed and quality. Code reviews, test writing, dependency hygiene, and CI/CD plumbing are high-value activities that consume significant engineering capacity. The Agentic Development Team externalises this mechanical overhead into an always-available, consistent agent fleet — reducing cycle time from requirement to deployed code while enforcing TDD, security scanning, and code quality gates on every change.

---

## System Context Diagram

```mermaid
C4Context
  title System Context — Agentic Development Team

  Person(engineer, "Engineer / Tech Lead", "Assigns tasks, reviews architectural decisions, approves production deployments")
  Person(product, "Product Owner", "Raises requirements via Jira tickets that the system acts on")

  System(devteam, "Agentic Development Team", "Autonomous multi-agent system that writes, tests, reviews, and deploys code across Go, TypeScript, JavaScript, Java, and Python")

  System_Ext(github, "GitHub / GitLab", "Version control, pull requests, code review, releases")
  System_Ext(jira, "Jira", "Issue tracking — source of task requirements and destination for status updates")
  System_Ext(sonar, "SonarQube", "Static analysis, security scanning, and code quality gates")
  System_Ext(jenkins, "Jenkins / GitHub Actions", "CI/CD pipeline execution and monitoring")
  System_Ext(slack, "Slack", "Human-facing notifications, escalations, and incident alerts")
  System_Ext(context7, "Context7 (Upstash)", "Up-to-date library and framework documentation for any version")
  System_Ext(vault, "HashiCorp Vault", "Secrets management — credentials injected at runtime, never stored in agent context")
  System_Ext(argocd, "ArgoCD", "GitOps reconciliation — applies infrastructure changes committed by the system")

  Rel(engineer, devteam, "Assigns tasks, approves deployments", "Chat / Jira / Slack")
  Rel(product, devteam, "Raises requirements", "Jira")
  Rel(devteam, github, "Manages branches, PRs, and releases", "GitHub MCP / REST")
  Rel(devteam, jira, "Creates, updates, and closes tickets", "Jira MCP / REST")
  Rel(devteam, sonar, "Runs static analysis and checks quality gates", "SonarQube MCP / REST")
  Rel(devteam, jenkins, "Triggers and monitors pipelines", "Jenkins MCP / REST")
  Rel(devteam, slack, "Sends status updates and escalations", "Slack MCP / REST")
  Rel(devteam, context7, "Fetches current library documentation", "MCP / REST")
  Rel(devteam, vault, "Retrieves secrets at runtime", "Vault API / TLS")
  Rel(devteam, argocd, "Commits infra changes; ArgoCD reconciles", "Git / REST")
```

---

## External Actors

| Name | Type | Interaction with System |
|---|---|---|
| Engineer / Tech Lead | Person | Assigns tasks in natural language; reviews and approves architectural decisions; approves production deployments via human-in-the-loop checkpoints |
| Product Owner | Person | Raises Jira tickets that the Orchestrator Agent reads as task requirements |
| GitHub / GitLab | External System | VCS host — the system manages branches, commits, pull requests, reviews, and releases via the GitHub/GitLab MCP server |
| Jira | External System | The system reads Jira tickets as task inputs and writes status updates, links, and comments back to tickets |
| SonarQube | External System | The Security and CI/CD Agents invoke SonarQube for SAST, SCA, and quality gate evaluation on every PR |
| Jenkins / GitHub Actions | External System | The CI/CD Agent triggers and monitors pipeline runs; pipeline failures are routed back to the responsible agent |
| Slack | External System | The Orchestrator sends task progress updates, escalations, and incident alerts to engineering Slack channels |
| Context7 (Upstash) | External System | All code-writing and infrastructure agents query Context7 before using any external library to retrieve version-accurate documentation |
| HashiCorp Vault | External System | All credentials (GitHub tokens, Jira API keys, SonarQube tokens, etc.) are stored in Vault and injected into agent containers at runtime; never present in agent context windows |
| ArgoCD | External System | The Infrastructure Agent commits Kubernetes manifest changes to the GitOps repository; ArgoCD detects and reconciles them to the cluster |

---

## System Boundary

Everything inside the "Agentic Development Team" box in the diagram is deployed within the organisation's Red Hat OpenShift AI cluster. This includes all agent containers, inference (vLLM) endpoints, the LangSmith observability instance, the vector store, and all MCP server containers. Nothing inside the boundary has direct internet access; all external system interactions are mediated through authenticated, audited MCP connections.
