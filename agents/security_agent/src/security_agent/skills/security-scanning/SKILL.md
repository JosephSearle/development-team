---
name: security-scanning
description: Perform SAST and dependency vulnerability analysis via SonarQube and GitHub MCP. Interpret scan findings, triage severity, propose remediations, and set quality gates. Use for any task involving security scanning, CVE triage, OWASP Top 10 analysis, or quality gate configuration.
allowed-tools: [sonarqube_get_issues, sonarqube_get_metrics, sonarqube_set_quality_gate, sonarqube_get_quality_gate_status, github_get_file_contents, github_list_commits]
---
## Severity Triage
- **Critical / High**: block merge; raise immediately; never suppress without written justification
- **Medium**: must be remediated within the sprint; add inline `# noqa: <rule>` only with a justification comment
- **Low / Info**: document in PR body; fix opportunistically

## OWASP Top 10 Quick Reference
- A01 Broken Access Control — check for missing authz guards on route handlers
- A02 Cryptographic Failures — flag use of MD5/SHA1 for secrets, hardcoded keys, weak TLS configs
- A03 Injection — flag unparameterised SQL, shell=True subprocess calls, unescaped template rendering
- A05 Security Misconfiguration — flag DEBUG=True in non-dev configs, open CORS wildcards
- A09 Logging Failures — flag logging of passwords, tokens, or PII

## Quality Gate Rules
- Do not lower an existing quality gate threshold without explicit human approval (`interrupt_on: sonarqube_set_quality_gate`)
- Always fetch current gate status before proposing changes

## Secrets Handling
- If `secrets_scanner` has already flagged secrets in the diff, do not proceed with SAST — return `scan_complete=False` and surface the secrets finding
