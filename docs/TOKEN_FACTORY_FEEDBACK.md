# Nebius Token Factory Developer Feedback & Experience Report

**Project:** ExcursionLens (Cold-Chain Excursion Forensic Agent)  
**Model Targeted:** `nvidia/llama-3.1-nemotron-70b-instruct`  
**Endpoint Base:** `https://api.tokenfactory.nebius.com/v1`  
**API Compatibility:** OpenAI v1 Chat Completions specification  

---

## 1. What Worked Exceptionally Well

1. **Seamless Drop-In API Compatibility:**
   - The standard `/v1/chat/completions` and `/v1/models` endpoints conform cleanly to the OpenAI specification.
   - Initializing the standard `AsyncOpenAI` client or standard `httpx` async calls required zero custom monkey-patching.

2. **Inference Latency & Throughput on NVIDIA Nemotron-70B:**
   - For a 70B parameter model, time-to-first-token (TTFT) and token generation velocity were outstanding. Multi-stage reasoning (generating three detailed competing causal hypotheses followed immediately by an adversarial critique pass) completed in under 4.5 seconds.
   - Streamed chunk responses over Server-Sent Events (SSE) remained stable without dropped frames or unexpected socket closures.

3. **Complex Instruction Following with Structured JSON:**
   - NVIDIA Nemotron demonstrated exceptional adherence to structured JSON schemas when instructed with system prompts requesting strict JSON outputs containing observation citations (`OBS-*`) and confidence ratings.
   - Unlike generic open-source instruction models, Nemotron consistently respected the negative constraint: refraining from hallucinating missing custody events and adhering strictly to the provided evidence packet.

---

## 2. Friction Points & Areas for Improvement

1. **Pre-flight Catalog Discovery & Model Naming Discrepancies:**
   - Querying `GET /v1/models` returns a diverse catalog of hosted open models. However, standardizing model IDs (e.g., whether `nvidia/llama-3.1-nemotron-70b-instruct` or alternative aliases are pinned to exact quantizations) would benefit from clearer catalog documentation.
   - Recommendation: Expose explicit metadata in the model object: quantization level (FP8/BF16), maximum context window, and recommended temperature range.

2. **Native JSON Schema Enforcement:**
   - While prompt-instructed JSON generation worked reliably, native support for `response_format: { type: "json_object" }` or structured schema validation (grammar-constrained decoding) would ensure zero JSON parse exceptions for mission-critical enterprise workflows.

3. **Rate Limit Transparency & Response Headers:**
   - Adding standard rate limit headers (`x-ratelimit-remaining-tokens`, `x-ratelimit-reset-requests`) on HTTP responses would allow clients to implement proactive exponential backoff before hitting 429 status codes.

---

## 3. Overall Verdict

Nebius Token Factory provides an enterprise-grade, cost-effective inference platform for running heavyweight frontier open weights like NVIDIA Nemotron-70B. It enabled ExcursionLens to deliver complex causal reasoning and adversarial critique in near-real-time without the overhead of self-hosting GPU infrastructure.
