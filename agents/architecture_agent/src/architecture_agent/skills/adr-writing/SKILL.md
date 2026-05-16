---
name: adr-writing
description: >
  How to research, evaluate, and document architecture decisions as ADRs. Covers
  the full lifecycle: identifying decision triggers, evaluating options against
  trade-off dimensions, writing the team ADR template, staging the file in
  workspace/adrs/, and requesting human approval before committing to the repo.
allowed-tools: [read_file, write_file, grep, glob, context7, github]
---

## ADR Lifecycle

1. **Trigger** — A decision is needed when two or more viable technical options exist and the choice has lasting consequences (framework selection, protocol, data model, deployment topology).
2. **Research** — Use the `library_researcher` sub-agent to fetch documentation for each candidate via Context7 in parallel.
3. **Evaluate** — Score each option across: performance, operational complexity, security posture, team familiarity, licence compatibility, community health.
4. **Draft** — Write the ADR to `workspace/adrs/NNNN-<slug>.md` using `write_file`.
5. **Interrupt** — Call `commit_file` to trigger the HITL interrupt. Do not proceed without human approval.
6. **Commit** — After approval, the orchestrator resumes and the file is committed to `docs/architecture/adr/`.

## ADR Template

```markdown
# NNNN — <Title>

**Status:** Proposed | Accepted | Superseded by MMMM

## Context

<Why is this decision needed? What constraints or requirements drive it?>

## Options Considered

### Option A — <Name>
<Description, pros, cons>

### Option B — <Name>
<Description, pros, cons>

## Decision

<Which option is chosen and why. Reference the evaluation dimensions.>

## Consequences

<What changes as a result? What becomes easier? What becomes harder?>
```

## Evaluation Dimensions

| Dimension | Weight | Notes |
|---|---|---|
| Performance | High | Latency, throughput at target scale |
| Operational complexity | High | Deployment, monitoring, on-call burden |
| Security posture | High | CVE history, SLSA level, supply chain |
| Team familiarity | Medium | Ramp-up time, existing expertise |
| Licence | Medium | OSS licence compatibility with product |
| Community health | Low | Stars, release cadence, maintainer responsiveness |

## Naming Convention

ADR files use zero-padded four-digit sequence numbers: `0001-adopt-langgraph.md`. Check existing ADRs in `docs/architecture/adr/` to determine the next number.
