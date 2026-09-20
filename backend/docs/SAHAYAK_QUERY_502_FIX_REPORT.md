# SAHAYAK — FINAL 502 / PROVIDER ERROR HANDLING AUDIT REPORT

## Final Error Semantics Audit

The backend exception handling in `api.py` has been explicitly audited and corrected to distinguish between different failure modes originating from the LLM provider, avoiding the catch-all `502` generic error.

- **429 (Too Many Requests)**: 
  - **What causes it**: This occurs when the provider enforces rate limits (e.g., token rate limits `rate_limit_exceeded`, `RateLimitError`).
  - **Mapping**: Handled properly and returned as HTTP `429`, prompting the frontend to display: "इन्टरनेट वा सर्भरमा समस्या देखियो। कृपया फेरि प्रयास गर्नुहोस्।"
- **413 (Payload Too Large)**: 
  - **What causes it**: This occurs when the context/history size exceeds the model's maximum allowed tokens (context overflow).
  - **Mapping**: Handled explicitly and mapped to HTTP `413` with the message: "कुराकानीको सन्देश धेरै लामो भयो। कृपया केही पुरानो सन्देश हटाएर वा नयाँ कुराकानी सुरु गरेर प्रयास गर्नुहोस्।" (Previously, this was incorrectly lumped into rate limit or generic 502).
- **504 (Gateway Timeout)**: 
  - **What causes it**: The provider is unresponsive or the request times out before completion.
  - **Mapping**: Explicitly caught and mapped to HTTP `504` with the message: "सर्भरले समयमा प्रतिक्रिया दिन सकेन। कृपया फेरि प्रयास गर्नुहोस्।"
- **502 (Bad Gateway)**: 
  - **What causes it**: General provider unavailability, connection failures, or upstream gateway issues.
  - **Mapping**: Mapped to HTTP `502` with the message: "Sahayak सेवा अहिले उपलब्ध छैन। कृपया केही समयपछि फेरि प्रयास गर्नुहोस्।"
- **500 (Internal Server Error)**: 
  - **What causes it**: Unexpected backend exceptions (e.g., database failures, internal logic bugs) that do not stem from provider API errors.
  - **Mapping**: Generic HTTP `500` stating: "सर्भरमा आन्तरिक समस्या देखियो।"

## Structured Fallback Safety

When the LLM fails to output valid JSON conforming to the `instructor` schema (e.g. returning `null` for a required `string` field), LiteLLM throws a validation error and falls back to a standard text completion without structured output.
- **Previous behavior**: This unvalidated raw text was erroneously wrapped into a verified `legal_answer`, which posed a safety risk by presenting unvalidated and potentially hallucinated provider text as a verified legal answer.
- **New behavior**: The fallback logic in `litellm_completion.py` now intercepts this raw text and wraps it in a **safe, non-assertive** `legal_clarification` response indicating that an answer could not be securely generated. 
- **Message provided**: `"तपाईंको प्रश्नको उत्तर तयार गर्दा समस्या भयो। कृपया प्रश्नलाई अलि स्पष्ट रूपमा लेख्नुहोस्।"` 
- **Safety Guarantee**: Unstructured provider failures will NEVER fabricate legal sections (like missing citations, acts, or procedures) or falsely classify text as a verified legal answer.

## Provider Availability

**Provider-connected E2E**: **PASS**

*(Note: The current model `qwen/qwen3.8-27b` has strict 7000 ITPM limits on the on-demand tier which we sometimes hit. When we do hit it, the updated system elegantly handles it via `429` as expected, rather than crashing with a `502`.)*

## Final Verification

- **flutter analyze**: PASS
- **flutter test**: PASS
- **flutter build web**: PASS
- **casual**: PASS (Verified HTTP 200 with `casual` response_type)
- **clarification**: PASS (Verified via standard query returning `legal_clarification`)
- **legal answer**: PASS (Verified `legal_answer` containing issues and context)
- **RAG**: PASS (Vector DB successfully returns authorized documents)
- **citations**: PASS (Valid chunk numbers and sources generated)
- **multi-turn**: PASS (History context maintains conversation flow)
- **429**: PASS (Correctly maps to rate limit message)
- **413**: PASS (Explicitly separated from 429)
- **502**: PASS (Reserved for upstream connection/gateway failures)
- **504**: PASS (Reserved for timeouts)
