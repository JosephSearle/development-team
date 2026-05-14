---
name: code-review
description: Review Python code systematically for correctness, security, test coverage, and style. Use read_file and grep to inspect files directly. Use GitHub MCP tools to read PR diffs. Output ONLY valid JSON matching the required schema.
allowed-tools: [read_file, glob, grep]
---
## Review Checklist
1. **Correctness**: does the implementation match the feature spec?
2. **Test coverage**: do tests cover happy path, edge cases, and error cases?
3. **Security**: no hardcoded secrets, no injection risks, no unsafe operations
4. **Type safety**: type annotations present and correct
5. **Style**: follows project conventions (ruff/mypy clean)

## Output format
Respond with ONLY valid JSON — no markdown, no prose before or after:
```json
{
  "approved": true,
  "reviewer_model": "<model-id>",
  "comments": ["..."],
  "blocking_issues": [],
  "metadata": {}
}
```

## Blocking conditions (approved: false)
- Missing tests for happy path or error cases
- Hardcoded secrets, credentials, or API keys
- SQL/command injection risk
- Type errors that mypy would flag
- Implementation does not satisfy the feature spec
