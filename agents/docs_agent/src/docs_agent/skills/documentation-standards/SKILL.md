---
name: documentation-standards
description: >
  Conventions for writing and maintaining project documentation: README structure,
  API reference format, changelog conventions (Keep a Changelog), and runbook
  standards. Covers what to draft locally versus what to commit directly via GitHub MCP.
allowed-tools: [read_file, write_file, grep, glob, github]
---

## File Layout

All documentation drafts go to `workspace/docs/` before committing. Commit only after
verifying content is complete and accurate.

## README Structure

```markdown
# <Project Name>

<One-sentence description.>

## Quick Start

<Minimum steps to run the project.>

## Configuration

<Environment variables, config files.>

## Development

<How to run tests, lint, build.>

## Architecture

<Link to C4 docs or brief description.>
```

## API Documentation

- Every public endpoint needs: method, path, request schema, response schema, and one example.
- Use OpenAPI-compatible Markdown tables where possible.
- Do not document internal or alpha endpoints without an `> **Experimental**` callout.

## Changelog Format (Keep a Changelog)

```markdown
# Changelog

## [Unreleased]

## [1.2.0] — YYYY-MM-DD
### Added
- <Feature>
### Changed
- <Change>
### Fixed
- <Fix>
```

## Runbook Structure

```markdown
# Runbook: <Incident Type>

## Symptoms
## Immediate Actions
## Root Cause Investigation
## Remediation Steps
## Escalation Path
## Post-Incident Actions
```

## Commit Convention

Use the GitHub MCP `create_or_update_file` tool to commit documentation.
Commit message format: `docs(<scope>): <short description>`.
