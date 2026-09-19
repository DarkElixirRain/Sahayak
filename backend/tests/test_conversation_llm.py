"""Conversation-engine tests for the grounded LLM pipeline (no database).

Uses a fake :class:`LLMProvider` and a patched retrieval layer, so every branch
of the pipeline can be asserted deterministically: grounded answers, missing
credentials, timeouts, malformed provider responses, unverified-only corpora,
retrieval failures, citation provenance, history handling and persistence.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import DatabaseUnavailableError
from app.schemas.conversation import ConversationResponse
from app.services.conversation import (
    STATUS_ANSWERED,
    STATUS_LLM_UNAVAILABLE,
    STATUS_NO_MATCH,
    STATUS_NO_VERIFIED_CONTEXT,
    STATUS_RETRIEVAL_ERROR,
    ConversationService,
)
from app.services.llm import (
    LLMMalformedResponseError,
    LLMProvider,
    LLMTimeoutError,
)

NEPALI_QUESTION = "मेरो भाइले मलाई मुद्दा हाल्यो, अब मैले के गर्नुपर्छ?"
ENGLISH_QUESTION = "What are my rights if my brother filed a case against me?"
GENERATED_ANSWER = "तपाईंको प्रश्नको आधारमा संरक्षक सम्बन्धी व्यवस्था लागू हुन्छ।"

ANALYSIS = {
    "intent": "legal_information",
    "domain": None,
    "entities": ["मुद्दा"],
    "query": NEPALI_QUESTION,
    "requires_clarification": False,
}


def _result(**overrides):
    row = {
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "provision_id": "prov-1",
        "document_title": "मुलुकी देवानी संहिता, २०७४",
        "section_number": "141",
        "section_title": "संरक्षक नियुक्ति",
        "content": "संरक्षक नियुक्त गर्दा व्यक्तिको इच्छा विचार गर्नुपर्ने।",
        "domain": "family",
        "source": "Nepal Law Commission",
        "source_id": "src-1",
        "source_type": "law_commission",
        "source_is_verified": True,
        "source_url": "https://example.invalid/141",
        "score": 1.1,
        "is_verified": True,
        "chunk_index": 1,
    }
    row.update(overrides)
    return row


def _retrieval(results=None, **overrides):
    results = [_result()] if results is None else results
    payload = {
        "query": NEPALI_QUESTION,
        "normalized_query": NEPALI_QUESTION.lower(),
        "tokens": ["भाइले", "मुद्दा", "हाल्यो"],
        "results": results,
        "total_found": len(results),
        "status": "ok",
        "verified_only": True,
        "unverified_match_count": 0,
    }
    payload.update(overrides)
    return payload


class FakeProvider(LLMProvider):
    """Records the prompts it receives and returns canned text."""

    name = "fake"
    model = "fake-model"

    def __init__(self, text: str = GENERATED_ANSWER, error: Exception | None = None):
        self.text = text
        self.error = error
        self.calls: list[dict] = []

    def generate(self, *, system_prompt, messages, temperature=0.0, max_tokens=900):
        self.calls.append({"system_prompt": system_prompt, "messages": messages})
        if self.error is not None:
            raise self.error
        from app.services.llm import LLMCompletion

        return LLMCompletion(text=self.text, provider=self.name, model=self.model)


def _conn_patch():
    """Patch the pooled connection used by the persistence step."""
    conn_cm = MagicMock()
    conn_cm.__enter__.return_value = "conn"
    conn_cm.__exit__.return_value = None
    return patch("app.services.conversation.get_connection", return_value=conn_cm)


def _service(provider=None, retrieval=None):
    service = ConversationService(provider=provider)
    # The service binds its repository class at construction time, so tests
    # swap the instance attribute instead of the module symbol.
    service.repository = MagicMock(name="repository")
    analysis_patch = patch.object(
        ConversationService, "analyze_question", return_value=dict(ANALYSIS)
    )
    retrieval_patch = patch.object(
        ConversationService, "retrieve_for_context", return_value=retrieval or _retrieval()
    )
    return service, analysis_patch, retrieval_patch


# --------------------------------------------------------------------------- #
# Grounded answer
# --------------------------------------------------------------------------- #

def test_grounded_answer_uses_llm_text_and_real_citations():
    provider = FakeProvider()
    service, analysis_patch, retrieval_patch = _service(provider)
    with analysis_patch, retrieval_patch:
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    model = ConversationResponse(**payload)
    assert model.status == STATUS_ANSWERED
    assert model.grounded is True
    assert model.generation == "llm"
    assert model.answer == GENERATED_ANSWER
    assert model.llm_provider == "fake"
    assert model.llm_model == "fake-model"

    assert len(model.citations) == 1
    citation = model.citations[0]
    assert citation.document_id == "doc-1"
    assert citation.provision_id == "prov-1"
    assert citation.chunk_id == "chunk-1"
    assert citation.section == "141"
    assert citation.section_title == "संरक्षक नियुक्ति"
    assert citation.source == "Nepal Law Commission"
    assert citation.source_url == "https://example.invalid/141"
    assert citation.is_verified is True
    assert citation.score == 1.1

    assert model.search_terms == ["भाइले", "मुद्दा", "हाल्यो"]


def test_provider_receives_the_context_and_the_question():
    provider = FakeProvider()
    service, analysis_patch, retrieval_patch = _service(provider)
    with analysis_patch, retrieval_patch:
        service.generate_grounded_response(NEPALI_QUESTION)

    call = provider.calls[0]
    system_prompt = call["system_prompt"]
    assert "संरक्षक नियुक्त गर्दा व्यक्तिको इच्छा विचार गर्नुपर्ने।" in system_prompt
    assert "Never invent a provision" in system_prompt
    assert "<legal_context>" in system_prompt

    assert len(call["messages"]) == 1
    assert NEPALI_QUESTION in call["messages"][0]["content"]
    assert call["messages"][0]["role"] == "user"


def test_retrieval_is_always_verified_only():
    provider = FakeProvider()
    service, analysis_patch, retrieval_patch = _service(provider)
    with analysis_patch, patch.object(
        ConversationService, "retrieve_for_context", return_value=_retrieval()
    ) as retrieve:
        service.generate_grounded_response(NEPALI_QUESTION)

    assert retrieve.call_args.kwargs["verified_only"] is True


def test_every_citation_maps_to_a_retrieved_row():
    results = [
        _result(),
        _result(chunk_id="chunk-2", provision_id="prov-2", section_number="142"),
    ]
    provider = FakeProvider()
    service, analysis_patch, retrieval_patch = _service(
        provider, retrieval=_retrieval(results)
    )
    with analysis_patch, retrieval_patch:
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    assert [c["chunk_id"] for c in payload["citations"]] == ["chunk-1", "chunk-2"]
    assert [c["provision_id"] for c in payload["citations"]] == ["prov-1", "prov-2"]
    assert all(c["is_verified"] for c in payload["citations"])


def test_citations_carry_source_traceability_from_the_database():
    provider = FakeProvider()
    service, analysis_patch, retrieval_patch = _service(provider)
    with analysis_patch, retrieval_patch:
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    citation = payload["citations"][0]
    assert citation["source_id"] == "src-1"
    assert citation["source_type"] == "law_commission"
    assert citation["source_is_verified"] is True


def test_citations_do_not_include_content_the_model_invented():
    """A model that invents an uncited provision must have its answer rejected."""
    provider = FakeProvider(
        text="धारा ९९९ र मुद्दा नम्बर १२३ का आधारमा निर्णय हुन्छ।"
    )
    service, analysis_patch, retrieval_patch = _service(provider)
    with analysis_patch, retrieval_patch:
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    # "धारा ९९९" is not in the retrieved evidence (only 141), so the answer is
    # rejected rather than presented: the fake citation never reaches the user.
    assert payload["status"] == STATUS_LLM_UNAVAILABLE
    assert payload["grounded"] is False
    assert payload["llm_error"] == "citation_validation_failed"
    assert len(provider.calls) == 1

    assert len(payload["citations"]) == 1
    assert payload["citations"][0]["section"] == "141"
    assert all(c["section"] != "999" for c in payload["citations"])
    assert "९९९" not in payload["answer"]
    assert "999" not in payload["answer"]


def test_unverified_rows_are_never_grounded_even_if_retrieval_returns_them():
    """Defence in depth: an unverified row cannot become a grounded answer."""
    provider = FakeProvider()
    unverified = _result(is_verified=False)
    service, analysis_patch, retrieval_patch = _service(
        provider, retrieval=_retrieval([unverified])
    )
    with analysis_patch, retrieval_patch:
        service.generate_grounded_response(NEPALI_QUESTION)

    # The provider is told the truth about the verification state, so it cannot
    # describe the material as verified.
    assert "0 of 1 context entries are marked VERIFIED" in provider.calls[0]["system_prompt"]
    assert "verification: UNVERIFIED" in provider.calls[0]["system_prompt"]


# --------------------------------------------------------------------------- #
# No verified context -> safe fallback
# --------------------------------------------------------------------------- #

def test_no_verified_context_never_calls_the_provider():
    provider = FakeProvider()
    retrieval = _retrieval(
        [],
        total_found=0,
        status="unverified_only",
        unverified_match_count=4,
    )
    service, analysis_patch, retrieval_patch = _service(provider, retrieval=retrieval)
    with analysis_patch, retrieval_patch:
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    assert provider.calls == [], "no context must never reach the model"
    assert payload["status"] == STATUS_NO_VERIFIED_CONTEXT
    assert payload["grounded"] is False
    assert payload["generation"] == "none"
    assert payload["citations"] == []
    assert payload["unverified_match_count"] == 4
    assert payload["retrieval_status"] == "unverified_only"
    assert "प्रमाणित" in payload["answer"]


def test_no_match_is_distinguished_from_unverified_only():
    service, analysis_patch, retrieval_patch = _service(
        FakeProvider(),
        retrieval=_retrieval([], total_found=0, status="no_match"),
    )
    with analysis_patch, retrieval_patch:
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    assert payload["status"] == STATUS_NO_MATCH
    assert payload["unverified_match_count"] == 0


def test_fallback_for_english_questions_is_english():
    service, analysis_patch, retrieval_patch = _service(
        FakeProvider(),
        retrieval=_retrieval([], total_found=0, status="no_match"),
    )
    with analysis_patch, retrieval_patch:
        payload = service.generate_grounded_response(ENGLISH_QUESTION)

    assert "could not find" in payload["answer"]
    assert all(q["question"].isascii() for q in payload["follow_up_questions"])
    assert "advice" in payload["disclaimer"]


# --------------------------------------------------------------------------- #
# Generation unavailable
# --------------------------------------------------------------------------- #

def test_missing_provider_returns_citations_without_an_answer():
    service, analysis_patch, retrieval_patch = _service(provider=None)
    with analysis_patch, retrieval_patch, patch(
        "app.services.conversation.get_llm_provider", return_value=None
    ):
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    assert payload["status"] == STATUS_LLM_UNAVAILABLE
    assert payload["generation"] == "unavailable"
    assert payload["grounded"] is False
    assert payload["llm_error"] == "not_configured"
    assert payload["llm_provider"] is None
    assert len(payload["citations"]) == 1, "real sources are still reported"
    assert "उत्तर निर्माण गर्ने सेवा उपलब्ध छैन" in payload["answer"]


@pytest.mark.parametrize(
    "error,expected_kind",
    [
        (LLMTimeoutError("slow"), "timeout"),
        (LLMMalformedResponseError("junk"), "malformed_response"),
    ],
)
def test_provider_failures_degrade_to_a_safe_response(error, expected_kind):
    service, analysis_patch, retrieval_patch = _service(FakeProvider(error=error))
    with analysis_patch, retrieval_patch:
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    assert payload["status"] == STATUS_LLM_UNAVAILABLE
    assert payload["llm_error"] == expected_kind
    assert payload["answer"] == payload["answer"]  # deterministic text
    assert "सेवा उपलब्ध छैन" in payload["answer"]


def test_retrieval_failure_returns_a_retrieval_error():
    provider = FakeProvider()
    service, analysis_patch, _ = _service(provider)
    with analysis_patch, patch.object(
        ConversationService,
        "retrieve_for_context",
        side_effect=DatabaseUnavailableError(),
    ):
        payload = service.generate_grounded_response(NEPALI_QUESTION)

    assert payload["status"] == STATUS_RETRIEVAL_ERROR
    assert payload["citations"] == []
    assert provider.calls == []
    assert "पहुँच हुन सकेन" in payload["answer"]


def test_no_branch_ever_fabricates_legal_content():
    """Every failure path returns empty citations and an explicit status."""
    for retrieval, expected in (
        (_retrieval([], total_found=0, status="no_match"), STATUS_NO_MATCH),
        (_retrieval([], total_found=0, status="unverified_only"), STATUS_NO_VERIFIED_CONTEXT),
    ):
        service, analysis_patch, retrieval_patch = _service(
            FakeProvider(), retrieval=retrieval
        )
        with analysis_patch, retrieval_patch:
            payload = service.generate_grounded_response(NEPALI_QUESTION)
        assert payload["status"] == expected
        assert payload["citations"] == []
        assert "धारा" not in payload["answer"] or "प्रमाणित" in payload["answer"]


# --------------------------------------------------------------------------- #
# Conversation memory
# --------------------------------------------------------------------------- #

def test_history_is_forwarded_and_the_current_question_is_not_duplicated():
    provider = FakeProvider()
    service, analysis_patch, retrieval_patch = _service(provider)
    history = [
        {"role": "user", "content": "पहिलो प्रश्न"},
        {"role": "assistant", "content": "पहिलो उत्तर"},
        {"role": "user", "content": NEPALI_QUESTION},  # just persisted
    ]
    with analysis_patch, retrieval_patch, _conn_patch(), patch.object(
        ConversationService, "get_conversation_context", return_value=history
    ):
        service.generate_grounded_response(NEPALI_QUESTION, session_id="s-1")

    messages = provider.calls[0]["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant", "user"]
    assert messages[0]["content"] == "पहिलो प्रश्न"
    assert messages[1]["content"] == "पहिलो उत्तर"
    # Exactly one copy of the current question.
    assert sum(NEPALI_QUESTION in m["content"] for m in messages) == 1


def test_history_handler_drops_empty_and_system_turns():
    service = ConversationService(provider=FakeProvider())
    history = [
        {"role": "user", "content": "पहिलो प्रश्न"},
        {"role": "assistant", "content": "   "},
        {"role": "system", "content": "internal note"},
    ]
    with patch.object(
        ConversationService, "get_conversation_context", return_value=history
    ):
        messages = service._history_messages("s-1", "new question")

    assert messages == [{"role": "user", "content": "पहिलो प्रश्न"}]


def test_history_failure_does_not_break_the_answer():
    provider = FakeProvider()
    service, analysis_patch, retrieval_patch = _service(provider)
    with analysis_patch, retrieval_patch, _conn_patch(), patch.object(
        ConversationService,
        "get_conversation_context",
        side_effect=RuntimeError("history unavailable"),
    ):
        payload = service.generate_grounded_response(NEPALI_QUESTION, session_id="s-1")

    assert payload["status"] == STATUS_ANSWERED


def test_history_is_capped():
    service = ConversationService(provider=FakeProvider())
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"turn {i}"}
        for i in range(20)
    ]
    with patch.object(
        ConversationService, "get_conversation_context", return_value=history
    ) as get_context:
        messages = service._history_messages("s-1", "new", max_messages=4)

    assert get_context.call_args.kwargs["max_messages"] == 4
    assert messages == [{"role": m["role"], "content": m["content"]} for m in history]


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #

def test_assistant_turn_is_persisted_as_the_answer_text():
    provider = FakeProvider()
    service, analysis_patch, retrieval_patch = _service(provider)
    repo = MagicMock()
    with analysis_patch, retrieval_patch, _conn_patch(), patch.object(
        service, "repository", MagicMock(return_value=repo)
    ):
        service.generate_grounded_response(NEPALI_QUESTION, session_id="s-1")

    repo.add_message.assert_called_once()
    kwargs = repo.add_message.call_args.kwargs
    assert kwargs["session_id"] == "s-1"
    assert kwargs["role"] == "assistant"
    assert kwargs["content"] == GENERATED_ANSWER


def test_fallback_turns_are_also_persisted():
    service, analysis_patch, retrieval_patch = _service(
        FakeProvider(), retrieval=_retrieval([], total_found=0, status="no_match")
    )
    repo = MagicMock()
    with analysis_patch, retrieval_patch, _conn_patch(), patch.object(
        service, "repository", MagicMock(return_value=repo)
    ):
        service.generate_grounded_response(NEPALI_QUESTION, session_id="s-1")

    repo.add_message.assert_called_once()
    stored = repo.add_message.call_args.kwargs["content"]
    assert stored.strip()
    assert "नेमोट्रॉन" not in stored
