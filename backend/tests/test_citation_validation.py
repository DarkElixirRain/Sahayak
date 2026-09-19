"""Phase 10 regression tests: citation & source verification guarantees.

These run without a database. They pin down the safety behaviour of the
grounded pipeline:

* Part 15 - an answer that cites a section absent from the retrieval results
  is rejected (a hallucinated "Section 999" never reaches the user).
* Part 16 – URLs and source attributions cannot be invented by the model on
  top of the database metadata; answer text never carries URLs.
* Part 8  - malformed source URLs are dropped, never emitted.
* Part 10 - currentness is preserved from document metadata, never guessed.
* Part 11 - citations are deduplicated on stable provision identity.
* Part 6  - verification state is propagated faithfully from the database row.

The retries/edge cases mirror the helpers used across the pipeline, so a
change in citation handling shows up here first.
"""

from unittest.mock import MagicMock, patch

from app.schemas.conversation import ConversationResponse
from app.services.conversation import (
    STATUS_ANSWERED,
    STATUS_LLM_UNAVAILABLE,
    STATUS_NO_MATCH,
    STATUS_NO_VERIFIED_CONTEXT,
    ConversationService,
)
from app.services.legal_grounding import build_citations
from app.services.llm import LLMCompletion, LLMProvider

NEPALI_QUESTION = "मेरो भाइले मलाई मुद्दा हाल्यो, अब मैले के गर्नुपर्छ?"

ANALYSIS = {
    "intent": "legal_information",
    "domain": None,
    "entities": ["मुद्दा"],
    "query": NEPALI_QUESTION,
    "requires_clarification": False,
}


def _result(**overrides):
    row = {
        "chunk_id": "chunk-42",
        "document_id": "doc-7",
        "provision_id": "prov-7",
        "document_title": "मुलुकी देवानी संहिता, २०७४",
        "section_number": "12",
        "section_title": "सम्पत्ति संरक्षण",
        "content": "सम्पत्ति संरक्षण सम्बन्धी व्यवस्था।",
        "domain": "family",
        "source_id": "src-a",
        "source": "नेपाल कानून आयोग",
        "source_type": "law_commission",
        "source_is_verified": True,
        "source_url": "https://law.gov.example/muluki-dewani-12",
        "document_status": "current",
        "document_effective_date": "2075-01-01",
        "score": 0.9,
        "is_verified": True,
        "chunk_index": 0,
    }
    row.update(overrides)
    return row


def _retrieval(results, **overrides):
    payload = {
        "query": NEPALI_QUESTION,
        "normalized_query": NEPALI_QUESTION.lower(),
        "tokens": ["भाइले", "मुद्दा"],
        "results": results,
        "total_found": len(results),
        "status": "ok",
        "verified_only": True,
        "unverified_match_count": 0,
    }
    payload.update(overrides)
    return payload


class FakeProvider(LLMProvider):
    name = "fake"
    model = "fake-model"

    def __init__(self, text):
        self.text = text
        self.calls = []

    def generate(self, *, system_prompt, messages, temperature=0.0, max_tokens=900):
        self.calls.append({"system_prompt": system_prompt, "messages": messages})
        return LLMCompletion(text=self.text, provider=self.name, model=self.model)


def _run(text, results=None):
    """Run one grounded generation with canned model output."""
    provider = FakeProvider(text)
    service = ConversationService(provider=provider)
    service.repository = MagicMock(name="repository")
    results = [_result()] if results is None else results
    with patch.object(
        ConversationService, "analyze_question", return_value=dict(ANALYSIS)
    ), patch.object(
        ConversationService,
        "retrieve_for_context",
        return_value=_retrieval(results),
    ):
        return provider, service.generate_grounded_response(NEPALI_QUESTION)


# --------------------------------------------------------------------------- #
# Part 15: hallucinated citations are rejected
# --------------------------------------------------------------------------- #

def test_devanagari_hallucinated_section_is_rejected():
    provider, payload = _run("धारा ९९९ ले यो अधिकार दिन्छ भन्ने देखिन्छ।")
    assert payload["status"] == STATUS_LLM_UNAVAILABLE
    assert payload["grounded"] is False
    assert payload["llm_error"] == "citation_validation_failed"
    assert "९९९" not in payload["answer"]
    assert "999" not in payload["answer"]
    assert len(provider.calls) == 1


def test_latin_hallucinated_section_is_rejected():
    provider, payload = _run("Under Section 999 of the Code the right exists.")
    assert payload["status"] == STATUS_LLM_UNAVAILABLE
    assert payload["llm_error"] == "citation_validation_failed"
    assert "Section 999" not in payload["answer"]
    assert len(provider.calls) == 1


def test_supported_section_mixed_with_hallucinated_one_is_rejected():
    _, payload = _run(
        "धारा १२ ले सम्पत्ति संरक्षण गर्छ, तर धारा 555 ले पनि लागू हुन्छ।"
    )
    assert payload["status"] == STATUS_LLM_UNAVAILABLE
    assert payload["llm_error"] == "citation_validation_failed"
    assert "555" not in payload["answer"]


def test_an_answer_that_only_references_retrieved_sections_is_accepted():
    for text in (
        "धारा १२ अनुसार सम्पत्ति संरक्षणको व्यवस्था छ।",
        "Section 12 protects the property under this act.",
    ):
        _, payload = _run(text)
        assert payload["status"] == STATUS_ANSWERED
        assert payload["grounded"] is True
        assert payload["citations"][0]["section"] == "12"


# --------------------------------------------------------------------------- #
# Part 16: fake sources / URLs cannot be invented
# --------------------------------------------------------------------------- #

def test_invented_source_url_is_stripped_from_the_answer():
    provider, payload = _run(
        "Section 12 applies. See the law at https://fake-attacker.example/steal"
    )
    model = ConversationResponse(**payload)
    assert model.status == STATUS_ANSWERED
    assert "http" not in model.answer
    assert "fake-attacker.example" not in model.answer
    # The citation carries only the URL that exists in the database.
    assert model.citations[0].source == "नेपाल कानून आयोग"
    assert model.citations[0].source_url == "https://law.gov.example/muluki-dewani-12"
    assert model.citations[0].source_id == "src-a"


def test_devanagari_digit_url_is_not_created_and_http_only():
    citation = build_citations([_result(source_url="ftp://law.gov.example/1212")])[0]
    assert citation["source_url"] is None


# --------------------------------------------------------------------------- #
# Part 10: currentness is preserved, never guessed
# --------------------------------------------------------------------------- #

def test_currentness_is_taken_from_document_metadata():
    citation = build_citations([_result(document_status="repealed")])[0]
    assert citation["currentness_status"] == "repealed"
    citation = build_citations([_result(document_status="")])[0]
    assert citation["currentness_status"] == "unknown"


# --------------------------------------------------------------------------- #
# Part 11: citations are deduplicated on provision identity
# --------------------------------------------------------------------------- #

def test_five_results_for_one_provision_yield_one_citation():
    rows = [
        _result(chunk_id=f"c-{i}") for i in range(5)
    ]
    citations = build_citations(rows)
    assert len(citations) == 1
    assert citations[0]["provision_id"] == "prov-7"


# --------------------------------------------------------------------------- #
# Part 6: verification state is propagated faithfully
# --------------------------------------------------------------------------- #

def test_verified_only_evidence_grounds_one_answer():
    _, payload = _run("धारा १२ अनुसार वर्णन गर।")
    model = ConversationResponse(**payload)
    assert model.status == STATUS_ANSWERED
    assert len(model.citations) == 1
    assert model.citations[0].is_verified is True
    assert model.citations[0].source_is_verified is True


def test_multiple_verified_provisions_are_all_cited():
    rows = [
        _result(provision_id="p-1", section_number="12", section_title="A"),
        _result(provision_id="p-2", section_number="13", section_title="B"),
    ]
    _, payload = _run("धारा १२ र १३ दुवै लागू हुन्छन्।", results=rows)
    model = ConversationResponse(**payload)
    assert model.status == STATUS_ANSWERED
    assert {c.section for c in model.citations} == {"12", "13"}
    assert all(c.is_verified for c in model.citations)


def test_unverified_row_never_shows_as_verified():
    citation = build_citations([_result(is_verified=False, source_is_verified=False)])[0]
    assert citation["is_verified"] is False
    assert citation["source_is_verified"] is False


def test_no_evidence_path_never_grounds_or_cites():
    provider = FakeProvider("irrelevant")
    service = ConversationService(provider=provider)
    service.repository = MagicMock(name="repository")
    with patch.object(
        ConversationService, "analyze_question", return_value=dict(ANALYSIS)
    ), patch.object(
        ConversationService,
        "retrieve_for_context",
        return_value=_retrieval([], total_found=0, status=STATUS_NO_MATCH),
    ):
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    assert provider.calls == []
    assert payload["status"] == STATUS_NO_MATCH
    assert payload["citations"] == []
    # The safe fallback must never invent a section reference.
    model = ConversationResponse(**payload)
    assert "धारा" not in model.answer
    assert "Section" not in model.answer