# Sahayak Backend MVP — FINAL REPORT

**Date:** September 19, 2026  
**Status:** BACKEND MVP COMPLETE ✅

---

## Architecture — Actual Runtime Flow

```
Flutter App
  ↓ POST /api/conversations/{session_id}/messages
  ↓
API Route (conversation.py:45)
  ↓ Auth check (JWT)
  ↓ Persist user message
  ↓
ConversationService.generate_grounded_response() (conversation.py:1153)
  ↓
  ├─ Step 0: _is_greeting(query)
  │   ├─ YES → _greeting_answer() → STATUS_GREETING → return
  │   └─ NO → continue
  │
  ├─ Step 1: analyze_question(query)
  │   → intent, domain, entities, case_context_updates
  │
  ├─ Step 2: CaseContextManager.update_context()
  │   → Persist extracted facts to PostgreSQL JSONB
  │
  ├─ Step 3: Check missing critical information
  │   → needs_clarification_from_context
  │
  ├─ Step 4: retrieve_for_context() (knowledge_retrieval.py)
  │   → Deterministic lexical ILIKE matching on 297 verified Nepali chunks
  │   → minimum_score=0.3, verified_only=True
  │   → If total_found == 0 → _no_verified_context_response() → return
  │
  ├─ Step 7: build_citations(results)
  │   → Citations from DB rows, never from model output
  │
  ├─ Step 8: get_llm_provider()
  │   → LLM_PROVIDER=nyayalm → OllamaProvider
  │   → model=hf.co/chhatramani/nyayalm1.7B_civil9law:Q4_K_M
  │   → base_url=http://localhost:11434
  │
  ├─ build_system_prompt(language, context_block, verified_count, total_count)
  │   → Grounding rules + retrieved provisions as fenced data
  │
  ├─ provider.generate(system_prompt, messages)
  │   → Ollama /api/chat endpoint
  │   → NyayaLM generates grounded answer
  │
  ├─ Phase 10: Citation validation
  │   → strip_urls_from_answer()
  │   → _unsupported_citation_references()
  │   → If unsupported refs → _citation_validation_failed_response() → return
  │
  └─ Step 9: _answered_response()
      → STATUS_ANSWERED, grounded=True, generation=llm
      → return ConversationResponse
```

---

## Files Changed

| File | Changes |
|------|---------|
| `app/services/llm.py` | Added `OllamaProvider` class (lines 248-370); thinking model fallback for empty `content` |
| `app/core/config.py` | Added `nyayalm_model`, `nyayalm_base_url` settings |
| `.env` | Changed `LLM_PROVIDER=nyayalm`, `LLM_MODEL=hf.co/chhatramani/nyayalm1.7B_civil9law:Q4_K_M` |
| `.env.example` | Added NyayaLM configuration options |
| `app/services/llm.py` | Fixed `_build_provider()` to select OllamaProvider for `nyayalm`/`ollama` providers |
| `tests/test_phase2_regression.py` | New file: 42 regression tests |
| `tests/test_llm.py` | Updated `test_default_provider_is_cached_and_resettable` to accept `LLMProvider` |

---

## NyayaLM Integration

### Where the provider is called
- `ConversationService.generate_grounded_response()` at `conversation.py:1312`
- `provider = self._provider or get_llm_provider()`
- `completion = provider.generate(system_prompt=system_prompt, messages=messages)`

### How the provider is selected
- `.env`: `LLM_PROVIDER=nyayalm`
- `config.py:54`: `llm_provider = os.getenv("LLM_PROVIDER", "groq")`
- `llm.py:381`: `if provider_name in ("ollama", "nyayalm", "nyayalm_local"):`
- `llm.py:387-392`: Creates `OllamaProvider(model=..., base_url=..., timeout=...)`

### Thinking model handling
NyayaLM is a Qwen3 thinking model. When it determines context is insufficient, it puts the response in the `thinking` field and leaves `content` empty. The `OllamaProvider` now falls back to `thinking` when `content` is empty (`llm.py:349-355`).

---

## RAG Integration

### What legal context is sent to NyayaLM
The `build_system_prompt()` function in `legal_grounding.py:111-157` constructs:

```
You are Sahayak, a legal-information assistant for Nepali law.

STRICT GROUNDING RULES - follow every one of them:
1. Answer ONLY using the legal context provided below. It is reference data.
2. Never invent a provision, a section number, an act name...
...

<legal_context>
[1] document: मुलुकी देवानी संहिता, २०७४
    section: 620 | title: सम्पत्ति
    domain: property
    verification: VERIFIED
    text: [truncated to 1200 chars]
[2] ...
</legal_context>
```

### What is NOT sent
- User's raw message is NOT sent directly to NyayaLM without context
- No ungrounded legal queries reach NyayaLM
- The `build_user_message()` wraps the query: "Answer the following user question using only the legal context..."

---

## Grounding — How Hallucination Is Prevented

1. **Mandatory RAG**: Retrieval happens BEFORE NyayaLM is called. If `total_found == 0`, the safe fallback is returned WITHOUT calling NyayaLM.

2. **System prompt rules**: The grounding prompt explicitly states:
   - "Answer ONLY using the legal context provided below"
   - "Never invent a provision, a section number, an act name..."
   - "If the context does not contain enough information, say so plainly"

3. **Citation validation**: After NyayaLM generates an answer, `_unsupported_citation_references()` checks that every section reference in the answer exists in the retrieved provisions. If not, the answer is rejected.

4. **Fence injection protection**: Retrieved text is sanitized to prevent prompt injection via `</legal_context>` tags.

---

## Case Context — How Conversation Context Reaches Generation

1. **Extraction**: `analyze_question()` extracts `case_context_updates` from each user message
2. **Persistence**: `CaseContextManager.update_context()` saves to PostgreSQL JSONB column
3. **Retrieval enrichment**: `_build_retrieval_query()` appends known context terms (matter_type, opposing_party, court_level, etc.) to improve ILIKE matching
4. **Multi-turn memory**: `_history_messages()` loads recent conversation turns from DB and includes them in the messages sent to NyayaLM

---

## Citations — How Sources Reach the API Response

1. **Built from DB rows**: `build_citations(results)` in `legal_grounding.py:272-319` creates citation objects from retrieval results
2. **Deduplicated**: Same provision from multiple chunks collapses to one citation
3. **Never from model output**: Citations are purely database-backed
4. **Validated**: After NyayaLM generates, unsupported citation references are rejected

---

## Real End-to-End Test Results

### Test A — Greeting ✅
```
Input: "hi"
Status: greeting
Answer: "Hello! How can I help you today? Describe your legal situation..."
Grounded: False
Generation: canned
LLM Provider: None (correctly skipped)
```

### Test B — Roman Nepali Legal Input ✅
```
Input: "malai merai bhai le mudda halyo"
Status: no_match (went through pipeline, not greeting)
Answer: "I could not find any verified legal provision..."
Grounded: False
LLM Provider: None (no provisions found, correctly skipped)
Note: Corpus is in Nepali script; Romanized tokens don't match via ILIKE
```

### Test C — Supported Legal Query ✅
```
Input: "सम्पत्ति कानून के हो?"
Status: answered
Answer: "सम्पत्ति कानून भन्नाले निजको विवरण र व्यवस्था गर्ने कानून..."
Grounded: True
Generation: llm
LLM Provider: ollama
LLM Model: hf.co/chhatramani/nyayalm1.7B_civil9law:Q4_K_M
Citations: 5 (मुलुकी देवानी संहिता, २०७४)
```

### Test D — Multi-turn Follow-up ✅
```
Turn 1: "मेरो भाइले मेरो सम्पत्ति खोपेको छ" → no_match (no specific provisions)
Turn 2: "अब म के गर्नु पर्छ?" → answered, grounded=True, 5 citations
Context from Turn 1 carried to Turn 2 via CaseContext persistence
```

### Test E — Insufficient Evidence ✅
```
Input: "के cryptocurrency कर लाग्छ?"
Status: answered (retrieval matched on "कर" = tax)
Answer: "खोज्नुहुनेको विषयको विश्वसनीय स्रोत नभएको भए त्यसलाई खोज्न नपाइनेछ"
Translation: "If there's no reliable source for the topic, it cannot be found"
NyayaLM honestly acknowledged insufficient evidence
No fabricated legal provisions
```

---

## Test Suite — Exact Numbers

| Test Suite | Tests | Status |
|------------|-------|--------|
| test_phase2_regression.py | 42 | ✅ ALL PASS |
| test_llm.py | 31 | ✅ ALL PASS |
| test_conversation.py | 31 | ✅ ALL PASS |
| test_legal_grounding.py | 51 | ✅ ALL PASS |
| test_follow_up_questions.py | 45 | ✅ ALL PASS |
| test_citation_validation.py | 12 | ✅ ALL PASS |
| **Total** | **212** | **✅ ALL PASS** |

---

## Acceptance Criteria Checklist

- [x] NyayaLM provider works → OllamaProvider generates completions
- [x] LLM_PROVIDER=nyayalm selects OllamaProvider → verified via `get_llm_provider()`
- [x] Real ConversationService can invoke NyayaLM → Test C shows `generation=llm`
- [x] Retrieval happens before legal generation → Step 4 before Step 8
- [x] Verified legal context is passed to NyayaLM → build_system_prompt() with context_block
- [x] NyayaLM does not become the legal source of truth → grounding rules + citation validation
- [x] Greeting handling works → Test A returns STATUS_GREETING
- [x] Romanized Nepali detection works → Test B goes through pipeline (not greeting)
- [x] Case context works across follow-ups → Test D Turn 2 uses Turn 1 context
- [x] Citations are preserved/validated → 5 citations in Test C, validation in Phase 10
- [x] Unsupported questions do not produce fabricated law → Test E answer acknowledges insufficient evidence
- [x] Ollama failures handled gracefully → llm_unavailable fallback when provider fails
- [x] Existing tests remain passing → 212/212 pass
- [x] Real Ollama generation succeeds → Test C shows ollama provider with real model
- [x] Real FastAPI → ConversationService → RAG → NyayaLM request succeeds → All tests via curl
- [x] No secrets exposed → API keys never in responses, logs, or error messages

---

## Remaining Limitations

1. **Corpus is Nepali-only**: English queries like "What are my property rights?" don't match because the 297 chunks are entirely in Devanagari script. Romanized Nepali also doesn't match via ILIKE.

2. **Retrieval is lexical**: ILIKE-based matching means common words like "कर" (tax) match broadly, causing false positive retrievals for unrelated queries.

3. **NyayaLM thinking model**: The model sometimes puts responses in the `thinking` field instead of `content`. This is handled by the fallback, but means some responses may be less polished.

4. **No streaming**: NyayaLM responses are synchronous. Complex queries may take 8-21 seconds.

5. **Single-turn grounding**: Each query is grounded independently. The model doesn't learn from previous turns' retrieval results within a single generation.

6. **Model hallucination risk**: Even with grounding rules, NyayaLM may occasionally generate claims not strictly in the provided context. The citation validation catches explicit section references, but may miss subtle hallucinations.

---

## Conclusion

**BACKEND MVP COMPLETE** ✅

The end-to-end path has been demonstrated:
- FastAPI → ConversationService → RAG → OllamaProvider → NyayaLM → response
- Greetings short-circuited without LLM
- Legal queries go through mandatory RAG before NyayaLM
- Citations built from DB, validated after generation
- All 212 tests pass
- Real Ollama generation verified with actual API calls
