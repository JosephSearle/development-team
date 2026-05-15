---
name: cicd-patterns
description: Manage CI/CD pipelines via Jenkins and GitHub MCP — trigger builds, monitor pipeline status, promote artifacts through environments, and diagnose build failures. Use for any task involving pipeline execution, deployment promotion, build log analysis, or release gating.
allowed-tools: [jenkins_trigger_build, jenkins_get_build_status, jenkins_get_build_log, jenkins_list_jobs, github_get_file_contents, github_create_or_update_file, github_list_workflow_runs, github_trigger_workflow]
---
## Pipeline Stages (standard)
1. `build` — compile / package
2. `test` — unit + integration
3. `scan` — SAST + dependency audit
4. `publish` — push image / artifact to registry
5. `deploy-staging` — apply to staging namespace
6. `smoke` — post-deploy health check
7. `deploy-production` — apply to production (requires `interrupt_on: trigger_production_deploy`)

## Deployment Rules
- Never trigger `deploy-production` without a human approval interrupt
- Always verify `deploy-staging` + `smoke` succeed before promoting to production
- Rollback procedure: re-trigger the previous successful build's `deploy-production` stage

## Build Failure Triage
1. Fetch the last 200 lines of the failing stage's log
2. Identify the root cause (compile error, test failure, network timeout, resource exhaustion)
3. If a flaky test: re-trigger once before escalating
4. If an infrastructure issue: escalate to the infrastructure agent via the orchestrator

## Artifact Versioning
- Semantic versioning: `MAJOR.MINOR.PATCH[-SNAPSHOT]`
- Tag format: `v<version>` (e.g. `v1.4.2`)
- Never overwrite an existing released tag
