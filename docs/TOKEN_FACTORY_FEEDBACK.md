# Nebius Token Factory Developer Architectural & Integration Notes

**Project:** ExcursionLens (Cold-Chain Excursion Forensic Agent)  
**Model Targeted:** `nvidia/llama-3.1-nemotron-70b-instruct` (or dynamic catalog match)  
**Endpoint Base:** `https://api.tokenfactory.nebius.com/v1`  
**API Specification:** OpenAI v1 Chat Completions specification  
*Designed to use NVIDIA Nemotron through Nebius Token Factory. Current committed execution evidence is fixture mode; live verification remains blocked pending credentials.*

---

## 1. Architectural Design & API Surface Compatibility

1. **Standard API Protocol Conformance:**
   - The `/v1/chat/completions` and `/v1/models` endpoints follow the standard OpenAI REST specification.
   - Initializing standard `httpx.AsyncClient` or OpenAI-compatible async calls integrates with standard bearer authentication and JSON payload contracts.

2. **Dynamic Model Discovery Design:**
   - ExcursionLens incorporates runtime model discovery: querying `GET /v1/models` before investigator invocation to dynamically identify active NVIDIA/Nemotron model identifiers rather than hardcoding a single static slug.

3. **Structured Output & Constraint Enforcement Architecture:**
   - The orchestration pipeline is architected around structured JSON schemas requesting strict outputs with observation citations (`OBS-*`) and confidence ratings.
   - Deterministic claims validation acts as a post-inference safeguard to enforce boundary invariants regardless of model output.

---

## 2. Integration Observations & Platform Recommendations

1. **Catalog Metadata Enrichment:**
   - In catalog discovery (`GET /v1/models`), exposing explicit metadata in the model object (quantization level, context window limits, and supported output constraints) provides clear capability matching for agentic runtimes.

2. **Native JSON Schema Enforcement:**
   - Native support for grammar-constrained decoding (e.g. `response_format` with strict JSON schemas) is recommended for high-reliability operational agents to prevent parsing failures before validation.

3. **Rate Limit Transparency:**
   - Providing standard rate limit headers (`x-ratelimit-remaining-tokens`, `x-ratelimit-reset-requests`) enables robust client-side backoff and jitter management in high-throughput workflows.

---

## 3. Deployment Summary

ExcursionLens is engineered with full architectural support for Nebius Token Factory and NVIDIA Nemotron. While local repository verification is conducted in deterministic fixture mode pending live provider credentials, the integration client, catalog auto-discovery, and fail-closed smoke verifier (`scripts/live_smoke.py`) are fully implemented and verified against mocked contracts.
