---
name: tdd-implementation
description: Implement Python code following TDD — reads failing tests with read_file, searches codebase patterns with grep/glob, writes minimal implementation that makes tests pass using write_file. Use for RED phase (write minimal code) and REFACTOR phase (improve readability without breaking tests).
allowed-tools: [read_file, write_file, edit_file, glob, grep, ls]
---
## Steps
1. `write_todos`: plan the implementation steps
2. `read_file` the test file at the path given in your instructions
3. `glob`/`grep` the workspace for similar patterns to follow
4. If the feature involves a named library, use Context7 tools to fetch current docs
5. `write_file` the minimal implementation that makes the tests pass
6. Never include secrets, credentials, API keys, or tokens in generated code

## Phases
- **RED**: Write the minimum code to make the failing tests pass. No extra features.
- **REFACTOR**: Improve readability and type annotations; all tests must still pass after changes.

## Conventions
- Use type annotations on all public functions
- Follow the existing naming and module structure in the workspace
- Never write tests — only implementation code
