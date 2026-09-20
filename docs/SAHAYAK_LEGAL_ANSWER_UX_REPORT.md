# Sahayak Legal Answer UX Report

## 1. Current Problem
The previous Sahayak UI returned large blocks of AI-generated text containing internal RAG terminology (e.g. "Retrieved Context"), raw Markdown, and UUIDs for citations. This provided a poor user experience and did not feel like a polished legal product. The user could be overwhelmed by a long paragraph that required significant reading to extract actionable value.

## 2. Root Cause
The backend `/query` endpoint was returning raw `text` completions designed for a generic LLM chat. The frontend was rendering the entire string indiscriminately inside a single chat bubble without any visual hierarchy or parsing logic.

## 3. Response Architecture
We modified the response contract between the frontend and the backend by utilizing LiteLLM's structured outputs (`response_schema`). The Flutter frontend now passes a JSON schema inside the `/query` payload, ensuring the LLM structures its answer into a predefined `LegalAnswer` format.

## 4. Structured Legal Answer Model
Implemented `StructuredLegalAnswer` and `ApplicableLaw` models in Dart:
- `summary`: Short, scannable initial answer.
- `issue`: The detected legal topic.
- `applicable_laws`: A list of explicitly verified acts, sections, and explanations.
- `explanation`: Detailed reasoning in simple Nepali.
- `next_steps`: Actionable advice.
- `clarifying_questions`: Contextual follow-ups.

## 5. Dhara/Dafa Verification
The AI prompt (`backend/core/services/sahayak_prompts.py`) was updated with strict instructions to **NEVER hallucinate** laws or section numbers, and to only extract them when explicitly verified in the retrieved context. If no section is verified, the UI gracefully falls back to indicating that more context is needed.

## 6. Citation Improvements
The raw UUID lists were replaced with an expandable `CitationsSection` widget. The sources are now neatly tucked away, keeping the main response concise while remaining fully transparent and accessible.

## 7. Flutter UI Components
Created a modular, reusable widget system:
- `StructuredMessageBubble`: Parses the JSON response and orchestrates the layout.
- Issue and Summary Cards for at-a-glance comprehension.
- Applicable Law Cards tailored for Nepali legal nomenclature.
- Actionable chips for `clarifying_questions` that automatically populate the input field when tapped.

## 8. AI Prompt Improvements
The `SAHAYAK_SYSTEM_PROMPT` was refined to instruct the model to separate factual law from generalized guidance, to summarize rather than regurgitate retrieved text, and to adhere to the requested JSON schema.

## 9. Fallback Handling
Backward compatibility is maintained. The `chat_models.dart` `ChatMessage` parser attempts to decode the `content` string into JSON. If it fails, or if it encounters older history, the `chat_screen.dart` correctly falls back to rendering standard rich-text bubbles.

## 10. Tests Performed
- `flutter analyze`: Verified code cleanliness (no errors, only existing deprecations).
- `flutter build web`: Verified successful build compilation.
- Simulated structure mapping: Confirmed the model maps JSON correctly.

## 11. Screens/UI Improvements
The chat interface now presents structured, distinct visual cards instead of massive grey text walls, adhering to the requested aesthetic.

## 12. Remaining Limitations
The LLM response time might slightly increase due to the overhead of enforcing strict JSON generation.

## 13. Final Status
COMPLETE

## Final Regression Verification

- **flutter analyze**: PASS (0 structural errors)
- **flutter test**: PASS (Verified string/malformed/empty `applicable_laws` parsing robustly in `chat_models_test.dart`)
- **flutter build web**: PASS
- **Chrome**: PASS (Verified E2E flow to the browser)
- **structured response**: PASS (Correctly maps to `StructuredMessageBubble` instead of raw text)
- **multi-turn**: PASS (Context preserved and rendered successfully)
- **Nepali**: PASS
- **Romanized Nepali**: PASS
- **English**: PASS
- **citations**: PASS (Expandable `CitationsSection` working properly)
- **applicable laws**: PASS (Safely displays only verified elements, omits empty cards)
- **malformed applicable_laws**: PASS (Tolerates strings as verified by `chat_models_test.dart`)
- **plain-text fallback**: PASS (Properly renders unstructured strings)
- **voice**: PASS
- **responsive UI**: PASS (No overflow on long texts or wide citations)
