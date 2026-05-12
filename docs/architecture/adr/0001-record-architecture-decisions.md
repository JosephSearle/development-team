# ADR 0001: Record Architecture Decisions

**Date:** 2026-05-12  
**Status:** Accepted  
**Deciders:** Engineering team

## Context

When making significant architectural decisions, we need a way to document what was decided, why, and what the trade-offs are. Without this, future maintainers must reverse-engineer intent from code, repeat discussions that have already been resolved, and cannot understand the constraints that shaped the current design.

For an agentic system with twelve specialist agents, four inference tiers, and dozens of cross-cutting concerns, the volume of decisions requiring justification is unusually high. Unrecorded decisions here carry an elevated cost: incorrect assumptions about model selection or agent communication patterns can result in costly refactoring of deeply coupled components.

## Decision

We will use Architecture Decision Records (ADRs), as described by Michael Nygard, to document all significant architectural decisions. ADRs are stored in `docs/architecture/adr/`, numbered sequentially, and kept in the repository alongside the code they describe.

## Rationale

ADRs are lightweight (one Markdown file per decision), version-controlled, discoverable by engineers (same repository as the code), and create an immutable historical record. Alternatives considered: wiki pages (not version-controlled with code, become stale silently), comments in code (not structured, hard to discover, don't survive refactoring), verbal agreement (lost when team members leave or the system is handed off).

## Consequences

### Positive
- Architectural decisions are discoverable without asking senior team members
- New engineers can understand why the system is built the way it is
- Decisions are immutable — accepted ADRs are superseded, not edited, preserving historical context
- The Architecture Agent is instructed to produce ADR stubs for all significant decisions, reducing the human overhead of ADR authoring

### Negative
- Requires discipline to write an ADR for every significant decision
- Team must agree on what counts as "significant"

### Neutral / Risks
- ADRs describe intent at the time of decision — reality may diverge; validate ADRs during architectural reviews (recommended every 6 months)
- The Architecture Agent produces ADR stubs; human engineers must review and accept them — do not merge agent-generated ADRs without review

## Related Decisions
- Supersedes: (none)
- Superseded by: (none)
