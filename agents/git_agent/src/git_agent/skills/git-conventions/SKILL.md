---
name: git-conventions
description: Manage Git operations via GitHub MCP — create branches, commit changes, open pull requests, and manage labels following conventional commit standards. Use for any task involving branch creation, commit authoring, PR creation, or repository state queries.
allowed-tools: [github_create_branch, github_create_pull_request, github_get_pull_request, github_list_commits, github_create_or_update_file, github_push_files, github_create_review, github_merge_pull_request]
---
## Conventional Commits
- Format: `<type>(<scope>): <subject>` — subject in imperative mood, lowercase, no trailing period
- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`
- Breaking change: append `!` after type, e.g. `feat!: drop Python 3.11 support`

## Branch Naming
- Features: `feat/<kebab-description>`
- Fixes: `fix/<kebab-description>`
- Use the `branch_name` provided in your instructions; do not invent one

## Pull Request Standards
- Title = the primary commit message (conventional commit format)
- Body: Summary section (what changed), Motivation section (why), Test Plan section (how to verify)
- Always request review after opening; never merge your own PR
- Set `draft=True` when implementation is incomplete

## Rules
- Never force-push to `main` or `master`
- One logical change per commit; squash fixups before opening the PR
- Always check for an existing open PR on the branch before creating a new one
