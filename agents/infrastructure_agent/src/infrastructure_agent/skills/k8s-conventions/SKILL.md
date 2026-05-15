---
name: k8s-conventions
description: Author and validate Kubernetes manifests following GitOps conventions — Deployments, Services, ConfigMaps, HorizontalPodAutoscalers, NetworkPolicies, and Kustomize overlays. Use for any task involving manifest authoring, resource sizing, namespace configuration, or GitOps commit preparation.
allowed-tools: [read_file, write_file, glob, grep, github_create_or_update_file, github_push_files, github_get_file_contents]
---
## Manifest Conventions
- API version: prefer `apps/v1` for Deployments, `v1` for core resources
- Labels: always include `app.kubernetes.io/name`, `app.kubernetes.io/component`, `app.kubernetes.io/part-of`
- Namespace: never use `default`; use the namespace provided in your instructions
- Image tags: never use `latest`; always pin to a digest or immutable semver tag

## Resource Sizing Defaults
- Requests: CPU `100m`, memory `128Mi`
- Limits: CPU `500m`, memory `512Mi`
- Override when the task specifies different sizing requirements

## GitOps Rules
- Write manifests to the `manifests/` directory in the workspace
- Never apply directly to the cluster; commit files to the GitOps repo via GitHub MCP
- Use Kustomize overlays (`base/` + `overlays/<env>/`) for multi-environment configs
- Never store secrets in manifests; use `ExternalSecret` or `SealedSecret` references

## Security Baseline
- Set `securityContext.runAsNonRoot: true` on all containers
- Set `securityContext.readOnlyRootFilesystem: true` where possible
- Add a `NetworkPolicy` allowing only required ingress/egress ports
