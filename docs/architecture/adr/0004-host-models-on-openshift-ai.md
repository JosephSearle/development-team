# ADR 0004: Host Models on Red Hat OpenShift AI

**Date:** 2026-05-12  
**Status:** Accepted  
**Deciders:** Engineering team

## Context

All LLM inference for the system must be self-hosted. Using managed inference services (OpenAI API, Anthropic API, Google Vertex AI) is not an option because: model weights must remain on-premises for data residency; the organisation requires control over the inference hardware allocation; and agent execution traces contain potentially sensitive code and business logic that must not be transmitted to third-party inference providers.

The organisation operates a Kubernetes-based infrastructure. The model-serving solution must integrate with Kubernetes-native tooling and be operable by platform engineers familiar with Kubernetes, not ML infrastructure specialists.

Fine-tuning LoRA adapters is planned for Phase 2 (6–12 weeks post-launch). The hosting platform must support fine-tuning workflows, not only inference serving.

Constraints:
- On-premises GPU hardware (A100 and T4 GPUs)
- Kubernetes-native operation (no separate ML cluster)
- Must support vLLM as the inference runtime (see [ADR-0003](0003-use-multi-lora-vllm-serving-strategy.md))
- Must support LoRA fine-tuning without a separate training platform
- Red Hat enterprise support is a preference

## Decision

We will use **Red Hat OpenShift AI** (RHOAI) as the model hosting platform, deploying vLLM inference endpoints as **KServe InferenceService** resources on the OpenShift cluster.

## Rationale

OpenShift AI provides a Kubernetes-native ML platform that integrates directly with the organisation's existing OpenShift cluster. Key capabilities that drove the selection:

- **KServe integration:** vLLM is a first-class supported runtime in RHOAI via KServe. InferenceService resources are standard Kubernetes CRDs, operable by platform engineers without ML expertise.
- **LoRA fine-tuning support:** RHOAI integrates `fms-hf-tuning` (an open-source fine-tuning library supporting QLoRA and expert-parallel distributed training). This avoids a separate training platform for Phase 2 adapter training.
- **ODF object storage:** OpenShift Data Foundation provides S3-compatible on-premises object storage for model weights and LoRA adapters, eliminating dependency on cloud object storage.
- **GPU Operator:** OpenShift's GPU Operator manages A100 and T4 GPU driver installation and resource scheduling natively.
- **Enterprise support:** Red Hat enterprise support covers both the platform and the model-serving runtime, reducing operational risk.

**Alternatives considered:**

- **Vanilla Kubernetes + KServe + MinIO:** Functionally equivalent but requires assembling and maintaining individual components (KServe, cert-manager, MinIO, GPU Operator) without a supported integrated stack. Rejected: higher operational overhead with no functional advantage for this organisation's skill set.

- **MLflow + custom serving:** MLflow provides experiment tracking but does not provide a production inference serving solution. Would require a separate serving layer (e.g., Seldon, BentoML). Rejected: more components to maintain, no Red Hat support.

- **NVIDIA NIM (inference microservices):** Provides optimised serving for specific NVIDIA-certified models. Rejected: limited model selection does not include all required models (Qwen3.5, Qwen2.5-Coder); less flexible than vLLM for multi-LoRA serving.

- **Managed services (OpenAI, Anthropic, etc.):** Rejected at the constraints level — data residency and security requirements prohibit use.

## Consequences

### Positive
- Single platform for both inference serving and fine-tuning — no separate training infrastructure required in Phase 2
- KServe InferenceService resources are standard Kubernetes objects — operable with standard kubectl/helm tooling
- Model weights stored in ODF (on-premises, S3-compatible) — no cloud egress for model loading
- Red Hat enterprise support covers the full stack
- KEDA integration for autoscaling inference replicas on GPU resource metrics is supported natively

### Negative
- OpenShift AI adds licensing cost on top of base OpenShift licensing
- RHOAI platform version updates must be coordinated with OpenShift cluster upgrades — cannot be updated independently
- GPU Operator and KServe configuration has a learning curve for engineers new to ML infrastructure
- `fms-hf-tuning` supports PyTorch FSDP and certain Hugging Face model families — verify Qwen model family compatibility before Phase 2 training begins

### Neutral / Risks
- RHOAI 2.x is the current stable version; the platform is actively developed. Monitor RHOAI release notes for vLLM runtime version updates that may conflict with the vLLM version pinned in our KServe InferenceService manifests.
- Fine-tuning workflows using accelerated expert-parallel distributed training (available in RHOAI as of March 2026) require validation on Qwen architecture models — this has not been done at the time of this ADR.

## Related Decisions
- Supersedes: (none)
- Superseded by: (none)
- Related: [ADR-0003](0003-use-multi-lora-vllm-serving-strategy.md)
