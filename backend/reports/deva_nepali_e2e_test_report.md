# Sahayak Devanagari Nepali E2E Test Report

## 1. Test Date

2026-09-19, 17:20–17:41 NPT (11:35–11:41 UTC). Raw request/response data preserved in
`backend/reports/deva_e2e_state.json`.

## 2. Environment

| Item | Value |
|---|---|
| Backend | `/Users/bishalchaudhary/Sahayak/backend`, git HEAD `b02563e` ("Phase 4" commit). `app/util/roman_to_deva.py` was an **untracked working-tree file** (not in HEAD) and was corrupted mid-edit (see §4.1). |
| Python | 3.12.13 (`backend/.venv`) |
| API | FastAPI 0.141.1, uvicorn 0.53.0 (in-process server started by the test harness) |
| DB driver | psycopg 3.3.5 + psycopg-pool 3.3.1 |
| Database | Neon cloud PostgreSQL (`neondb`); host redacted. Corpus: **297 knowledge_chunks, all 297 `is_verified = TRUE`**, document status `current`, source `नेपाल कानून आयोग (Nepal Law Commission)`, source_url `https://lawcommission.gov.np/content/13455/civil-code-2074` |
| LLM provider | `LLM_PROVIDER=nyayalm` → `OllamaProvider` at `http://localhost:11434` |
| NyayaLM model | `hf.co/chhatramani/nyayalm1.7B_civil9law:Q4_K_M` (Qwen3 1.72B, 40960 ctx) |
| Endpoint tested | `POST /api/conversations/{session_id}/messages` (plus `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/conversations/{session_id}`) |
| Retrieval config | `minimum_score=0.3`, `verified_only=True`, `top_k=5` — **inspected and NOT changed** (route passes 0.3; the service hardcodes `verified_only=True`) |
| Secrets | None included in this report |

## 3. Test Objective

Evaluate whether the frozen Sahayak backend MVP, exercised as a real legal assistant over
HTTP, can: understand natural Devanagari Nepali legal questions, retrieve relevant **verified**
legal material, produce answers grounded in that material with valid citations, maintain
multi-turn case context, ask useful clarifying questions, refuse unsupported questions (no
invented laws/sections/deadlines/procedures), avoid exposing NyayaLM internal `thinking`, and
safely handle greetings.

## 4. Test Methodology

* All tests went through the **real FastAPI pipeline over HTTP**: `register → login (JWT) →
  POST /api/conversations/{session_id}/messages` with `Authorization: Bearer`. Message
  persistence, ownership checks, `ConversationService`, RAG, citation building, and NyayaLM
  generation were the production code paths. Nothing was mocked or stubbed.
* Harness: `backend/scripts/run_deva_e2e.py` (new test-harness file, not production code). It
  starts uvicorn in-process, runs one phase per invocation, and merges raw results into
  `backend/reports/deva_e2e_state.json`. Because each phase restarts the server process, the
  multi-turn test also exercised persistence across restarts.
* **Citation verification**: for every citation in a grounded response, the harness queried
  `knowledge_chunks` by the citation's `chunk_id` (joined to `legal_documents`,
  `legal_provisions`, `sources`) and compared document title, provision number, provision
  title, `is_verified`, and document status against the cited values.
* **NyayaLM thinking check**: a direct probe of Ollama `/api/chat` (same endpoint/payload shape
  the backend uses) recorded whether Ollama returns a separate `thinking` field; the API
  response schema was checked for any thinking exposure; grounded answers were compared
  against the provider's `content` field.
* No expected answers were hard-coded, no corpus/threshold changes were made, and no answer
  paths were bypassed.

## 5. Test Cases

Outcome labels are copied from the API (`status` field). Latency is client-observed.

### TEST A — Inheritance/property dispute

```text
Test ID: TEST_A_INHERITANCE
User input: मेरो भाइले हाम्रो बुबाको नाममा रहेको जग्गा आफ्नो नाममा राख्न खोजिरहेको छ। हामी दुई जना दाजुभाइ हौँ। बुबाको मृत्यु भइसकेको छ। यस्तो अवस्थामा मैले के गर्न सक्छु?
HTTP/API status: 200
Assistant response: "मेरो हालको ज्ञानभण्डारमा तपाईंको प्रश्नसँग मिल्ने प्रमाणित कानूनी प्रावधान भेटिएन, त्यसैले म अनुमान गरेर उत्तर दिन्नँ। …" (honest no-match fallback)
Status: no_match (mapped: no_match)
RAG retrieved: no (retrieval_total_found=0, unverified_match_count=0)
Verified context: no
Citation count: 0
Citation validity: NOT APPLICABLE (no citations produced)
Case context used: yes — matter_type="land" (from जग्गा), opposing_party="brother" (from भाइ) were extracted and enrichment terms (भूमि/land/अंशबाँडा/उत्तराधिकार/partition/inheritance) were appended to the retrieval query
NyayaLM used: no (no verified context → generation skipped)
Thinking exposed: no
Practical suggestions: follow_up_questions = ["के भयो भनेर संक्षेपमा बताउनुहोस्।" (missing_incident_description), "यो मुद्दा कुन जिल्ला वा शहरसँग सम्बन्धित छ?" (missing_location)]
Are suggestions supported by retrieved context: no citations existed; questions are intake prompts, not legal claims
Hallucination detected: no fabricated law. Observed problem: the follow-up "के भयो भनेर संक्षेपमा बताउनुहोस्" asks the user to describe what happened **even though the user had just described it in detail** — the incident_description extractor matches only Romanized verb tokens (gareko/halyo/bhayeko…), which never match Devanagari script input.
Missing information: no verified provision on अंशबाँडा/उत्तराधिकार/नामसारी was in the corpus under those exact Devanagari forms (DB check: "अंशबाँडा" → 0 verified chunks; "अंशबण्डा" → 0; "उत्तराधिकार" → 1; "जग्गा" → 3)
Overall observation: Retrieval found 0 verified matches for a realistic, fully-specified inheritance/property dispute; the fallback was honest and safe, but the system could not serve one of its core target scenarios. The enrichment terms generated by case context (अंशबाँडा, उत्तराधिकार) do not exist in the verified corpus in those forms, so enrichment could not help.
```

### TEST B — Property कब्जा

```text
Test ID: TEST_B_KABJA
User input: मेरो भाइले मेरो जग्गा कब्जा गरेको छ। अब मैले के गर्नुपर्छ?
HTTP/API status: 200
Assistant response: honest no-match fallback (same text as Test A)
Status: no_match
RAG retrieved: no (total_found=0, unverified=0)
Verified context: no
Citation count: 0
Citation validity: NOT APPLICABLE
Case context used: yes — opposing_party="brother", matter_type="land" extracted; partition/inheritance enrichment appended (visible in search_terms)
NyayaLM used: no
Thinking exposed: no
Practical suggestions: same two intake follow-ups as Test A
Are suggestions supported by retrieved context: no citations existed
Hallucination detected: no invented filing procedure or deadline (nothing was asserted)
Missing information: system did not ask about ownership documents or the nature of the कब्जा (it asked generic incident/description instead)
Overall observation: The corpus contains 4 verified chunks containing "कब्जा", yet retrieval returned 0 at minimum_score=0.3. The query was diluted across ~10 tokens (भाइले, जग्गा, कब्जा, गर्नुपर्छ, भूमि, land, अंशबाँडा, उत्तराधिकार, partition, inheritance): per-term scoring divides content hits by token count, so a chunk containing only "कब्जा" scores ≈ 1/10 = 0.1 < 0.3 and is filtered out. Factually observed: relevant verified material exists but is unreachable at the current threshold with multi-token natural questions.
```

### TEST C — Loan/debt

```text
Test ID: TEST_C_LOAN
User input: मैले एक जना व्यक्तिलाई रु ५ लाख सापटी दिएको थिएँ। उसले पैसा फिर्ता गर्दिनँ भनिरहेको छ। लिखित कागज पनि छ। अब कानुनी रूपमा के गर्न सक्छु?
HTTP/API status: 200
Assistant response: honest no-match fallback
Status: no_match
RAG retrieved: no (total_found=0, unverified=0)
Verified context: no
Citation count: 0
Citation validity: NOT APPLICABLE
Case context used: partially — matter_type/opposing_party were NOT extracted for this query (no "जग्गा"/"भाइ" style keywords); search_terms show the raw 18 query tokens with no enrichment
NyayaLM used: no
Thinking exposed: no
Practical suggestions: intake follow-ups only (same generic pair)
Are suggestions supported by retrieved context: no citations existed
Hallucination detected: no invented limitation period or deadline (nothing asserted)
Missing information: system did not recognize the debt/loan issue, did not ask about the written document beyond the generic prompt
Overall observation: "सापटी" → 0 verified chunks; "ऋण" → 22 verified chunks exist. The lexical gap between the user's word (सापटी) and the corpus vocabulary (ऋण) was not bridged, so the verified debt material was unreachable. Devanagari digit "५" and currency "रु" tokens passed through as search terms without effect.
```

### TEST D — Assault

```text
Test ID: TEST_D_ASSAULT
User input: मेरो छिमेकीले मलाई कुटपिट गरेको छ। मेरो शरीरमा चोट लागेको छ र अस्पतालको रिपोर्ट पनि छ। अब मैले कहाँ उजुरी गर्नुपर्छ?
HTTP/API status: 200
Assistant response: honest no-match fallback
Status: no_match
RAG retrieved: no (total_found=0, unverified=0)
Verified context: no
Citation count: 0
Citation validity: NOT APPLICABLE
Case context used: no location/court/authority extracted (छिमेकी/प्रहरी not matched by extractor patterns for this input; "प्रहरी" appears nowhere in the query). user_role="self" style extraction did not produce stored fields for this turn in its own session.
NyayaLM used: no
Thinking exposed: no
Practical suggestions: intake follow-ups only
Are suggestions supported by retrieved context: no citations existed
Hallucination detected: no invented police/court procedure, no invented deadline (nothing asserted)
Missing information: system did not answer "कहाँ उजुरी गर्नुपर्छ" and did not explain that it could not
Overall observation: "कुटपिट" → 0 verified chunks. The criminal-law side of the verified corpus (फौजदारी कार्यविधि / संहिता material) either is not present under these Devanagari forms or is unreachable at this threshold. The safe fallback prevented fabrication, which is correct behavior, but the user's direct procedural question went unanswered.
```

### TEST E — Unsupported/insufficient evidence (Bitcoin tax rate) — CRITICAL

```text
Test ID: TEST_E_BITCOIN_TAX
User input: नेपालमा Bitcoin बाट कमाएको पैसामा अहिले कति प्रतिशत कर लाग्छ?
HTTP/API status: 200
Assistant response: honest no-match fallback ("मेरो हालको ज्ञानभण्डारमा … प्रमाणित कानूनी प्रावधान भेटिएन, त्यसैले म अनुमान गरेर उत्तर दिन्नँ।")
Status: no_match
RAG retrieved: no (total_found=0, unverified=0)
Verified context: no
Citation count: 0
Citation validity: NOT APPLICABLE
Case context used: no (correct — nothing to extract)
NyayaLM used: no (generation never invoked — the model physically could not invent a percentage)
Thinking exposed: no
Practical suggestions: intake follow-ups only
Are suggestions supported by retrieved context: no citations existed
Hallucination detected: NO tax percentage was invented. The response correctly stated that available verified material does not establish the requested figure.
Missing information: the corpus contains no Bitcoin-specific source (DB check: "Bitcoin" → 0 verified chunks)
Overall observation: This is the exact failure mode the task warned about ("कर" matches 249 verified chunks), and the system handled it CORRECTLY in this run: although the token "कर" was in the query, the score dilution across 8 tokens meant generic कर provisions scored below 0.3 and returned nothing, so the model was never given generic tax text it could have misused. The lexical-dilution weakness and the grounding guard effectively cancelled out here — the safe outcome was reached, but via threshold arithmetic rather than source-specific verification. A query with fewer tokens (e.g. "कर कति प्रतिशत लाग्छ?") would likely have retrieved generic कर provisions; that behavior was NOT tested in this run and is NOT VERIFIED.
```

### TEST F — General legal question

```text
Test ID: TEST_F_PROPERTY_LAW_GENERAL
User input: सम्पत्ति कानून भनेको के हो?
HTTP/API status: 200
Status: answered (grounded=True, generation=llm, confidence=medium)
RAG retrieved: yes (total_found=31 verified matches; top 5 sent to model)
Verified context: yes (all 5 context entries VERIFIED)
Citation count: 5
Citation validity: all 5 verified against the database (see §7) — 100% match on document/section/verification
Case context used: enrichment appended जग्गा/property terms (visible in search_terms)
NyayaLM used: yes (ollama, NyayaLM 1.7B Q4_K_M, latency 23.2 s)
Thinking exposed: no (answer equals provider message.content; no thinking text in response)
Practical suggestions: ["यस मुद्दामा अर्को पक्ष को हो?" (missing_opposing_party), "के भयो भनेर संक्षेपमा बताउनुहोस्।" (missing_incident_description)] — intake prompts; no legal claims
Are suggestions supported by retrieved context: no citations relied upon; questions are neutral
Hallucination detected: no invented sections. Observed quality problem: the user asked "what is property law?" and the answer summarized provisions about inheritance (हकवाला) determination under foreign law (content of दफा 695/707) instead of defining property law. The response also ends abruptly mid-sentence (output token limit). Every cited section is real and retrieved, so the grounding guard held; the mismatch is a retrieval-relevance + small-model summarization issue, not citation fabrication.
Missing information: no verbatim provision text or quotes were included in the answer
Overall observation: This was the ONLY test that produced a grounded LLM answer. Citation machinery performed correctly end-to-end. Answer relevance to the actual question was poor.
```

Assistant response (full text, TEST F):

> सम्पत्ति कानून भन्नाले त्यस्तो सम्पत्तिको बसोबास गर्ने विदेशीको हकवाला निर्धारण गर्ने विदेशी कानून बमोजिम गरिने र त्यसरी नागरिकता पहिचान हुन नसकेमा जुन मुलुकमा निजको सामान्य बसोबास रहेको छ सोही मुलुकको कानून बमोजिम हकवाला निर्धारण गरिने अर्थले उल्लेख गरिएको छ।
>
> **स्पष्ट व्यवस्था:**
> 1. **विदेशी कानून बमोजिम हकवाला निर्धारण** — …
> 2. **नागरिकता पहिचान नभएमा मुलुकको कानून** — जुन मुलुकमा निजको सामान्य बसोबास रहेको छ त्यो
>
> (ends mid-sentence)

### CLARIFICATION TEST

```text
Test ID: CLARIFICATION_VAGUE
User input: मेरो जग्गाको विषयमा समस्या भयो। अब के गर्ने?
HTTP/API status: 200
Status: no_match (needs_clarification=true, confidence=low)
RAG retrieved: no (total_found=0; search_terms: जग्गाको, विषयमा, समस्या, भूमि, land)
Citation count: 0
Follow-up questions: ["यस मुद्दामा अर्को पक्ष को हो?" (missing_opposing_party), "के भयो भनेर संक्षेपमा बताउनुहोस्।" (missing_incident_description)]
Evaluation: The system did not produce a confident legal conclusion (correct). The clarification questions are substantively useful (identifies opposing party, asks for the incident) but not tailored to property disputes (did not ask about ownership documents, land type, or nature of the problem). Because no verified material was found for the vague query either, the user received BOTH a "no verified provision" fallback AND intake questions — an acceptable, honest combination.
Hallucination detected: no
```

### GREETING TESTS

```text
Test ID: GREETING_1
User input: नमस्ते
HTTP/API status: 200
Status: greeting | RAG retrieved: no | NyayaLM used: no | latency 3.7 s
Assistant response: "नमस्ते! Hello, ma kasari sahayog garna sakchhu? तपाईंको कानूनी समस्या बताउनुहोस्, …" (friendly, non-legal, no citations)
Observed problem: the response mixes Devanagari, Romanized Nepali ("ma kasari sahayog garna sakchhu?") and English in one sentence; the follow_up_questions field still contained two legal intake questions ("यो के प्रकारको मुद्दा हो…", "यस मुद्दामा अर्को पक्ष को हो?") even though needs_clarification=false. Greeting short-circuit itself worked: no retrieval, no LLM call.

Test ID: GREETING_2
User input: हेलो, सन्चै हुनुहुन्छ?
HTTP/API status: 200
Status: no_match | RAG retrieved: no (total_found=0) | NyayaLM used: no | latency 6.9 s
Assistant response: the legal "no verified provision" fallback text ("मेरो हालको ज्ञानभण्डारमा … प्रमाणित कानूनी प्रावधान भेटिएन, त्यसैले म अनुमान गरेर उत्तर दिन्नँ।")
Observed problem: a pure pleasantry was NOT recognized as a greeting (the greeting list contains "नमस्ते"/"नमस्कार" and Romanized variants, but not "हेलो" or "सन्चै हुनुहुन्छ") and fell through to the legal pipeline, producing the exact confusing behavior the greeting short-circuit was built to prevent: the user is told no verified legal provision matched their hello. Retrieval and LLM were not invoked (fallback at no_match), so no fabrication occurred.
```

## 6. Multi-turn Conversation Results

Session: client id `e2e-deva-multiturn-a424ce`; each turn sent through the real endpoint;
each turn handled by a **freshly restarted server process** (phased harness), so persistence
across restarts was genuinely exercised.

| Turn | Input | status | RAG | Citations |
|---|---|---|---|---|
| 1 | मेरो भाइले हाम्रो बुबाको नाममा रहेको जग्गा आफ्नो नाममा राख्न खोजिरहेको छ। | no_match | 0 | 0 |
| 2 | बुबाको मृत्यु भइसकेको छ र हामी दुई जना दाजुभाइ हौँ। | no_match | 0 | 0 |
| 3 | अब मैले के गर्नुपर्छ? | no_match | 0 | 0 |
| 4 | कुन कागजात चाहिन्छ? | no_match | 0 | 0 |
| 5 | यदि भाइले मेरो कुरा मानेन भने? | no_match | 0 | 0 |

**Context extracted and persisted (verified in DB, `conversation_sessions.case_context` JSONB
for this session, `updated_at` advanced from 11:38:51Z to 11:40:11Z across turns):**

```json
{
  "user_role": "self",
  "matter_type": "land",
  "opposing_party": "brother",
  "court": null, "district": null, "incident_description": null, "...": "all other fields null"
}
```

* Context **persisted**: yes — the JSONB row was created on turn 1 and updated through turn 5
  (turn 5 re-matched "भाइ" → opposing_party=brother).
* Context **retrieved**: yes — enrichment terms (जग्गा, भूमि, land, अंशबाँडा, उत्तराधिकार,
  partition) appear in `search_terms` on every later turn, including short turns 3–5 which
  contain no legal vocabulary of their own. Turn 3 ("अब मैले के गर्नुपर्छ?") was searched with
  the accumulated property/partition terms, not treated as an unrelated question.
* Relevant legal context: none found — every turn returned `no_match` (see §5/§9 for cause).
* Response grounding: every turn gave the honest no-verified-provision fallback; no invented
  law at any turn.
* Citations: none (nothing retrieved).
* Follow-up repetition: turns 1–5 all returned the identical pair of intake questions; the
  case context knew matter_type/opposing_party were already answered, yet the question
  catalogue kept asking "के भयो भनेर संक्षेपमा बताउनुहोस्" and "यो मुद्दा कुन जिल्ला…" because
  `incident_description`/`location` extraction never fires for Devanagari text.
* History endpoint: `GET /api/conversations/{session_id}` → 200, `message_count: 10`
  (5 user + 5 assistant turns persisted).
* SQL-level note: the production schema stores `session_id` as `uuid`; ad-hoc SQL equality on
  the client string failed with "invalid input syntax for type uuid". The repository layer
  resolves client session ids correctly (API behavior above was consistent), but I could not
  directly match the client string to the row via raw SQL — mapping mechanism NOT VERIFIED at
  SQL level, verified at API level.

**Conclusion:** case-context memory works at the data layer (extraction → JSONB persistence →
retrieval-query enrichment across restarts). It did not produce a usable legal conversation in
this run because retrieval found nothing for any turn.

## 7. Citation Verification

All citations produced during the whole test run came from TEST F (5 citations). Each was
checked against the live `knowledge_chunks` row by `chunk_id`:

| # | Cited (doc / section / title) | DB row found | DB is_verified | DB provision number | DB document status | Doc match | Section match |
|---|---|---|---|---|---|---|---|
| 1 | मुलुकी देवानी संहिता, २०७४ / 620 / अचल सम्पत्तिको लिज करार सम्बन्धी विशेष व्यवस्था | yes | true | 620 | current | yes | yes |
| 2 | मुलुकी देवानी संहिता, २०७४ / 707 / स्वामित्वको अन्तरवस्तु सम्पत्ति रहेको मुलुकको कानून बमोजिम हुने | yes | true | 707 | current | yes | yes |
| 3 | मुलुकी देवानी संहिता, २०७४ / 63 / सम्पत्ति छुट्याउनु पर्ने | yes | true | 63 | current | yes | yes |
| 4 | मुलुकी देवानी संहिता, २०७४ / 695 / हकवालाको निर्धारण विदेशी कानून बमोजिम गरिने | yes | true | 695 | current | yes | yes |
| 5 | मुलुकी देवानी संहिता, २०७४ / 42 / कानूनी व्यक्तिले सक्षमता प्राप्त गर्ने | yes | true | 42 | current | yes | yes |

Result: **5/5 citations traced to real, verified database rows with exact document/section
matches.** No fabricated section numbers appeared in any response. No citation was produced
anywhere else in the test run (all other outcomes were no_match with empty citation lists),
so no other citation could be verified — none existed.

## 8. Unsupported Query Results

The Bitcoin/tax test (TEST E) is documented in §5. Summary of what was actually verified:

* The question retrieved **zero** verified provisions (`total_found=0`,
  `unverified_match_count=0`, `status=no_match`) despite "कर" appearing in 249 verified
  corpus chunks — token dilution kept generic tax chunks below `minimum_score=0.3`.
* The user-facing answer invented **no** percentage, **no** law, **no** deadline; it stated
  plainly that no verified provision was found.
* NyayaLM was never invoked for this question, so the small model had no opportunity to
  hallucinate a rate.
* Caveat recorded honestly: the safe outcome came from score arithmetic, not from any
  Bitcoin-specific check. A shorter query heavy on "कर" was not part of this test run, so
  behavior in that case is NOT VERIFIED.

## 9. Hallucination / Unsupported Claim Findings

No invented law, section, deadline, or procedure was emitted in any of the 15 API
conversations (9 single + 5 multi-turn + greeting). Observed problems, stated plainly:

1. **TEST F — answer/question mismatch (grounded but irrelevant).** The answer summarized
   foreign-law inheritance determination (content of retrieved दफा 695/707) instead of
   explaining what सम्पत्ति कानून is. All citations were real; the generative layer produced
   content that was traceable but did not address the question. The answer also truncated
   mid-sentence (output token cap), an observable quality defect.
2. **GREETING_2 treated as a legal query.** "हेलो, सन्चै हुनुहुन्छ?" produced the legal
   "no verified provision" fallback. Not a hallucination, but a wrong-register response that
   reads as a bug to a user.
3. **GREETING_1 mixed scripts** ("नमस्ते! Hello, ma kasari sahayog garna sakchhu? …") and
   attached legal intake questions to a greeting.
4. **Repetitive generic follow-ups despite complete narratives.** TEST A and every multi-turn
   turn asked "के भयो भनेर संक्षेपमा बताउनुहोस्" after the user had already described the
   incident. Root cause (code-inspected, not modified): `_extract_case_context` matches only
   Romanized verb tokens (gareko/halyo/bhayeko/…), which never occur in Devanagari input, so
   `incident_description` is never captured and the follow-up catalogue keeps requesting it.
5. **No unverified leakage.** `unverified_match_count=0` everywhere; all 297 corpus chunks are
   verified, so the `verified_only=True` guard had nothing to filter in this run — its
   filtering behavior under mixed data is NOT VERIFIED here (covered by unit tests instead).

## 10. Backend Regression Tests

Executed: `cd backend && .venv/bin/python -m pytest tests/ -q`

```text
511 passed, 67 skipped in 125.87s
```

Skips: 66 × `TEST_DATABASE_URL not configured` (integration tests require a separate test
database URL) + 1 × `live LLM test: set SAHAYAK_LIVE_LLM=1`. These are pre-existing,
intentional skips, not failures.

**Blocking defect found before this suite could run at all** (see §4.1): with the corrupted
working-tree file present, pytest failed at collection with `SyntaxError: '[' was never
closed` — zero tests could execute. The 511-passed result above is from **after** the minimal
repair; the pre-repair result was a collection error.

## 11. API E2E Results

| Check | Result |
|---|---|
| `POST /api/auth/register` | 200 |
| `POST /api/auth/login` (OAuth2 form) | 200, JWT received |
| `POST /api/conversations/{id}/messages` × 15 (Devanagari bodies, UTF-8) | 200 every time |
| Message persistence | verified via `GET /api/conversations/{id}` → 200, `message_count: 10` for the 5-turn session |
| Ownership enforcement | second user's `GET` on first user's session → **403** `Not authorized to access this conversation` |
| Latency | no_match path ≈ 7–8.5 s; grounded path ≈ 23 s (NyayaLM on CPU/Metal) |
| Malformed/edge inputs | not tested in this run (out of scope) |

The full chain HTTP → FastAPI → auth → persistence → ConversationService → RAG → citations →
NyayaLM executed end-to-end on every legal question.

### 4.1 Blocking infrastructure defect (only code change made — documented per instructions)

During initial inspection the backend could not even be imported, so no test in this task was
possible:

* **File changed:** `backend/app/util/roman_to_deva.py` (untracked working-tree file; not in
  git HEAD)
* **Exact change:** added the missing closing `]` for the `_SYLLABLE_RULES` list literal
  (line ~445): `    (re.compile(r"^kanoonwala$"), "कानूनवाला"),` followed by `]`. Nothing
  else was altered. The file's garbled `_VOWEL_SIGNS` line (contains a replacement-character
  `�`) was left untouched — it is syntactically valid and the module is never called in the
  retrieval path.
* **Reason it was necessary:** `app/services/conversation.py` line 62 imports this module at
  module load; the `SyntaxError` crashed every import path (`app.main`, pytest collection,
  uvicorn). This is a genuine blocking defect, not a behavioral one.
* **Why safe:** code search shows the three imported functions
  (`build_dual_script_query`, `normalize_romanized_nepali`, `is_romanized_nepali`) are
  imported but **never called** anywhere in `app/` — restoring importability changes no
  runtime behavior. Post-fix smoke test: `build_dual_script_query("मेरो जग्गा")` returns input
  unchanged (Devanagari passthrough).
* **Tests before:** `pytest` → collection `SyntaxError` (0 tests run). **Tests after:**
  511 passed, 67 skipped.
* No other production file was modified. No thresholds, corpus, prompts, or answer logic were
  touched.

Observation (no action taken): during the run, the Neon connection pool intermittently raised
`DatabaseUnavailableError` on the first request(s) of a fresh process; requests succeeded
after retry. This affected the harness, not correctness of any recorded response. Possible
pool warm-up/race issue worth investigating later.

## 12. Findings

### Working

* Retrieval → grounding → citation machinery is internally consistent: every citation emitted
  (5/5) traced to a real verified DB row with exact document/section match; zero fabricated
  sections across all runs.
* Honest fallbacks: every question that could not be grounded received the explicit
  "no verified provision — I will not guess" response in Nepali; the unsupported Bitcoin
  question produced no invented tax rate.
* Case-context extraction and persistence works across turns and across process restarts
  (user_role/matter_type/opposing_party stored in JSONB; enrichment terms reached the
  retrieval query on later short turns).
* Greeting short-circuit works for exact greetings (नमस्ते): no RAG, no LLM call, friendly
  non-legal reply.
* Auth + ownership: JWT flow works; cross-user session access correctly rejected with 403.
* Message persistence: full user/assistant history retrievable via the status endpoint.
* Regression suite: 511 passed / 67 pre-existing skips.

### Problems Found

1. **Retrieval coverage failure on realistic Devanagari questions (most severe).** 5 of 6
   substantive legal questions returned `no_match` even where related verified material
   exists (कब्जा: 4 chunks exist but unreachable; सापटी vs ऋण vocabulary gap; कुटपिट: 0
   chunks; अंशबाँडा/उत्तराधिकार enrichment terms absent from corpus in those forms). The
   core promise — natural Nepali question → verified legal answer — did not hold for
   inheritance, कब्जा, loan, or assault scenarios in this run.
2. **Score dilution at `minimum_score=0.3`.** Per-term scoring divides content hits by total
   token count; a 10-token natural question scores ≈0.1 for a chunk matching one distinctive
   legal term, below threshold. Single distinctive terms (कब्जा) cannot surface through
   multi-token queries. (Observed empirically; consistent with the scoring SQL.)
3. **Devanagari incident descriptions never captured**, causing repetitive "के भयो?"
   follow-ups after full narratives (extractor only matches Romanized verb tokens).
4. **Grounded-but-irrelevant generation** (TEST F): question/answer mismatch plus mid-sentence
   truncation from the token cap.
5. **Greeting detection too narrow**: "हेलो, सन्चै हुनुहुन्छ?" fell into the legal pipeline
   and returned the legal no-match text; "नमस्ते" reply mixes three scripts and carries legal
   intake questions.
6. **Corpus vocabulary mismatch with user language**: user-facing terms (सापटी, कुटपिट,
   अंशबाँडा) largely absent from the verified corpus (ऋण exists; कब्जा exists but unreachable
   per #2).
7. **`OllamaProvider` thinking-fallback risk (code-inspected, not triggered):** when Ollama
   returns empty `content`, the provider substitutes the `thinking` field as the answer. The
   probe confirmed NyayaLM does return a separate English `thinking` field ("Okay, the user is
   asking about…"). In this run `content` was always non-empty, so **no thinking reached users**
   — but the fallback path would expose internal reasoning if triggered.
8. **Flaky first-request DB pool behavior** in fresh processes (harness-visible; possible
   warm-up race).

### Potential Improvements

* Add a Nepali synonym/expansion layer for retrieval (सापटी↔ऋण, कुटपिट↔कुट, अंशबाँडा↔अंशबण्डा/
  फाँटवारी) or normalize corpus + query terms; the corpus uses "अंशबण्डा" spellings while the
  enrichment map uses "अंशबाँडा".
* Revisit per-token score dilution (e.g., max-term scoring, IDF weighting, or a lower threshold
  for distinctive single terms) without weakening the verified-only guard.
* Add Devanagari verb/action patterns to `_extract_case_context` so incident descriptions are
  captured for Devanagari input.
* Extend greeting list (हेलो, सन्चै हुनुहुन्छ?, ठीक छ) and make the greeting reply
  single-script.
* Remove or gate the Ollama `thinking`-as-content fallback; treat empty content as
  `malformed_response` instead of exposing reasoning text.
* Investigate the first-request connection-pool failure mode.
* Consider raising the generation output cap for Nepali answers (truncation observed).

## 13. Backend MVP Status

Based strictly on this run's evidence: the backend can be treated as a **frozen MVP whose
safety architecture works but whose core retrieval value proposition did not, for natural
Devanagari Nepali questions, in this test**. Concretely:

* It never fabricated law, never exposed thinking, never leaked unverified content, enforced
  ownership, and degraded safely in every failure case — the safety contract held 100%.
* It produced a grounded, correctly-cited answer for exactly **1 of 6** substantive legal
  questions (the most generic one). The other 5 returned honest "I found nothing" fallbacks,
  and the 5-turn inheritance conversation never surfaced relevant verified law despite related
  provisions existing in the corpus.
* The multi-turn case-context layer functioned mechanically but could not convert context into
  a useful answer while retrieval returned nothing.

Calling this "production-ready for Nepali legal Q&A" would not be supported by this evidence.
The honest framing is: safe, well-instrumented, correctly-guarded pipeline whose retrieval and
answer-relevance layers need focused work before the product delivers value on its primary
use case.

## 14. Recommended Next Development Phase

1. **Retrieval quality phase (highest priority).** Build a Devanagari evaluation set (the six
   questions in this report plus more), measure hit/miss against the verified corpus, and
   address the vocabulary gap (synonym normalization) and score dilution. Success metric:
   relevant verified provisions retrieved for Tests A–D/F-style questions without relaxing
   `verified_only`.
2. **Corpus completion audit.** Inventory which user-facing Devanagari legal terms have zero
   verified chunks (कुटपिट, सापटी, अंशबाँडा/अंशबण्डा, नामसारी, प्रहरी उजुरी procedures) and
   prioritize importing those verified sources.
3. **Answer relevance phase.** After retrieval improves, evaluate NyayaLM answer relevance vs
   the question (not just citation validity) and the 900-token truncation behavior for Nepali.
4. **UX-safety polish.** Greeting coverage, single-script greeting reply, Devanagari incident
   extraction to stop repetitive follow-ups.
5. **Hardening.** Remove the Ollama thinking-fallback path; add a warm-up health check or
   retry for the DB pool; add integration tests for the session_id uuid mapping observed in
   this run.
6. **Re-run this exact E2E suite** (`backend/scripts/run_deva_e2e.py`, raw state in
   `backend/reports/deva_e2e_state.json`) after each phase to measure deltas with the same
   yardstick.
