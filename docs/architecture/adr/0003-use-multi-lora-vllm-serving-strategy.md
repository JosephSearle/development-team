# ADR 0003: Use Multi-LoRA vLLM Serving Strategy

**Date:** 2026-05-12  
**Status:** Accepted  
**Deciders:** Engineering team

## Context

The system's twelve agents have different inference requirements. The Code Agent and Test Agent benefit significantly from a code-specialist model, while the Orchestrator, Architecture Agent, and Code Review Agent need strong general reasoning. Utility agents (Git, CI/CD, Docs, Infra, Dependency) need reliable instruction following but not cutting-edge reasoning.

An early design considered running a separate model for each agent or agent class. With twelve agents and five target programming languages, a fully separated model approach would require between 4 and 12 independently deployed LLMs, with a corresponding GPU footprint, operational overhead, and deployment complexity that is not justified by the marginal quality improvement.

Additionally, for code generation tasks, language-specific fine-tuning is expected to improve output quality for internal codebases and conventions. This fine-tuning must be possible without replacing the base model.

Constraints:
- GPU budget is limited: the organisation has a defined A100/H100 GPU allocation
- Fine-tuning must be possible incrementally as training data accumulates
- New language specialisations must be addable without infrastructure changes
- All models must run on self-hosted OpenShift AI — no managed inference services

## Decision

We will serve three base models across four vLLM endpoints, using **multi-LoRA adapter switching** on the Code Tier endpoint to deliver language-specific specialisation from a single 32B model deployment.

The four endpoints are:
1. **Reasoning Tier** — Qwen3.5-72B-Instruct (2× A100 80GB, tensor parallel)
2. **Code Tier** — Qwen2.5-Coder-32B-Instruct with multi-LoRA (1× A100 80GB)
3. **Utility Tier** — Qwen2.5-14B-Instruct (1× A100 40GB)
4. **Guardrail Tier** — Llama-Guard-3-8B (T4 GPU)

## Rationale

**Multi-LoRA vs. separate models:** vLLM supports dynamic LoRA adapter loading at inference time (enabled with `--enable-lora`). Multiple adapters can be served from a single base model instance; the correct adapter is selected per-request based on a tag in the request. At inference time, only the adapter weights are swapped — not the base model. This delivers language-specific fine-tuning with near-zero additional GPU memory overhead compared to the base model alone. The alternative (one model per language) would require 5× the GPU allocation for the Code Tier alone.

**Three tiers vs. one universal model:** A single large model (e.g., Qwen3.5-72B for all agents) was evaluated but rejected. The Utility Tier agents (Git, CI/CD, Docs, Infra, Dependency) primarily make structured tool calls from well-defined prompts. Running these on a 72B model wastes GPU capacity and increases per-call latency compared to a 14B model. The quality difference for structured tool-use tasks is marginal.

**Model selection — Qwen3.5-72B for Reasoning:** Selected over DeepSeek-V4-Pro (80.6% SWE-bench) due to lower GPU requirement (Qwen3.5-72B with MoE active-parameter efficiency fits on 2× A100 80GB; DeepSeek-V4-Pro requires more memory). DeepSeek-V4-Pro remains the preferred alternative if GPU budget expands.

**Model selection — Qwen2.5-Coder-32B for Code:** Top open-source code-specialist model on HumanEval, MBPP, and SWE-bench Lite benchmarks as of early 2026. Supports all five target languages. 128K context window accommodates large file reads. StarCoder 2 was evaluated but rejected — lower benchmark scores than Qwen2.5-Coder at the same parameter count.

**Model selection — Llama-Guard-3-8B for Guardrail:** Purpose-built for content and safety classification; far more efficient than using a general-purpose model for this role. 8B parameters runs on a T4 GPU, keeping guardrail latency low and not consuming A100 capacity.

## Consequences

### Positive
- GPU footprint is significantly lower than a per-agent or per-language model approach
- New language LoRA adapters can be added by uploading to ODF and updating the KServe InferenceService manifest — no base model redeployment
- LoRA fine-tuning on internal codebases can be performed incrementally using OpenShift AI's fms-hf-tuning without disrupting inference
- vLLM prefix caching reduces TTFT for repeated system prompts across the high-volume Code Tier
- Clean separation of concerns: model quality improvements are isolated to a tier, not a full system upgrade

### Negative
- LoRA adapter files must be managed as versioned artifacts in ODF — requires an adapter release process
- Multi-LoRA adapter swap adds latency (~1–2s) on the Code Tier when switching between languages at high throughput; pre-loading all adapters at start mitigates this if it becomes a bottleneck
- Reasoning Tier runs a single 72B model instance; horizontal scaling requires additional 2× A100 GPU pairs — cost scales quickly
- Initial launch has no language-specific LoRA adapters (base model only); adapter quality improvement is deferred to Phase 2

### Neutral / Risks
- LoRA adapter quality depends on training data quality. A miscalibrated adapter could silently produce lower-quality output than the base model. Mitigated by: eval dataset validation before promotion; staged rollout (staging before production); human approval for adapter promotion.
- vLLM multi-LoRA is a production feature as of vLLM 0.4+ but relatively new. Monitor vLLM release notes for breaking changes to the LoRA serving API.

## Related Decisions
- Supersedes: (none)
- Superseded by: (none)
- Related: [ADR-0002](0002-adopt-deepagents-langgraph-for-agent-orchestration.md), [ADR-0004](0004-host-models-on-openshift-ai.md)
