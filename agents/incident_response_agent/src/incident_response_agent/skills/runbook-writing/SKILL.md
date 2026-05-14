---
name: runbook-writing
description: >
  Incident response process and runbook documentation standards. Covers the
  triage workflow, Kubernetes log query patterns, Jira incident ticket format,
  when to escalate, and the runbook Markdown template for post-incident records.
allowed-tools: [read_file, grep, glob, github, jira, kubernetes]
---

## Incident Triage Workflow

1. **Acknowledge** — Confirm alert receipt; note timestamp and affected service.
2. **Scope** — Determine blast radius: which users, regions, or services are affected.
3. **Parallel diagnostics** — Invoke `log_analyzer` and `metrics_analyzer` sub-agents simultaneously; wait for both.
4. **Hypothesise** — Form top-3 root cause hypotheses ranked by likelihood.
5. **Verify** — Use Kubernetes MCP (read-only) and GitHub to confirm or eliminate each hypothesis.
6. **Remediate** — Propose remediation steps; create Jira issue for human approval before execution.
7. **Document** — Write runbook capturing timeline, root cause, and prevention steps.

## Kubernetes Log Query Patterns

Use the `kubernetes` MCP tool `get_pod_logs` with:
- `namespace`: affected namespace
- `label_selector`: e.g. `app=auth-service`
- `tail_lines`: 200 (start narrow, expand if needed)
- `since_seconds`: 3600 (last hour)

Look for: OOMKilled, CrashLoopBackOff, ImagePullBackOff, connection refused, timeout.

## Jira Incident Ticket Format

```
Summary: [P<severity>] <Service>: <brief description>
Priority: Critical | High | Medium | Low
Labels: incident, <service-name>, <environment>
Description:
  ## Impact
  <affected users/services, business impact>

  ## Timeline
  <key timestamps>

  ## Root Cause
  <hypothesis or confirmed cause>

  ## Remediation
  <steps taken or proposed>
```

## Escalation Matrix

| Severity | Criteria | Escalation |
|---|---|---|
| P1 | Full outage or data loss risk | Page on-call lead immediately |
| P2 | Degraded service >10% users | Notify team channel; create P2 Jira |
| P3 | Minor degradation | Create Jira; fix in next sprint |
| P4 | Cosmetic / no user impact | Log ticket; no escalation |

## Runbook Template

```markdown
# Runbook: <Incident Title>

**Date:** YYYY-MM-DD  **Severity:** P<N>  **Jira:** <URL>

## Symptoms
## Timeline
## Root Cause
## Remediation Steps Applied
## Prevention
## Action Items
```
