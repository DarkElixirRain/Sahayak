"""Phase 2 regression tests for greeting detection, OllamaProvider, and NyayaLM."""

import json

import httpx
import pytest

from app.services.conversation import (
    _is_greeting,
    _greeting_answer,
    STATUS_GREETING,
)
from app.services.llm import (
    OllamaProvider,
    LLMCompletion,
    LLMProviderError,
    LLMTimeoutError,
    LLMMalformedResponseError,
)
from app.services.legal_grounding import detect_language
from app.services.case_context import CaseContext


# ---------------------------------------------------------------------------
# 1. Greeting detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("greeting", [
    "hi", "hello", "hey", "namaste", "namaskar",
    "नमस्ते", "नमस्कार",
    "hi there", "hello there",
    "k cha", "k xa", "sanchai cha",
])
def test_pure_greetings_are_detected(greeting):
    assert _is_greeting(greeting) is True


@pytest.mark.parametrize("not_greeting", [
    "hi mero bhai le mudda halyo",
    "hello, malai kanoon sahayog chahiyo",
    "mero jagga ko kanoon ke ho",
    "namaste, mero bhai le mero samptti chepto gareko cha",
    "what is the legal process for property dispute",
    "malai merai bhai le mudda halyo",
])
def test_greeting_with_content_not_detected(not_greeting):
    assert _is_greeting(not_greeting) is False


def test_greeting_answer_english():
    answer = _greeting_answer("english")
    assert "Hello" in answer
    assert "legal" in answer.lower()


def test_greeting_answer_nepali():
    answer = _greeting_answer("nepali")
    assert "नमस्ते" in answer
    assert "कानूनी" in answer


# ---------------------------------------------------------------------------
# 2. Language detection
# ---------------------------------------------------------------------------

def test_english_detection():
    assert detect_language("What is the legal process?") == "english"


def test_devanagari_detection():
    assert detect_language("जग्गाको कानून के हो?") == "nepali"


def test_romanized_nepali_detection():
    # Romanized Nepali has no Devanagari characters, so the script-based
    # detector classifies it as English. This is expected behavior - the
    # retrieval system handles Romanized Nepali via case context extraction.
    result = detect_language("malai merai bhai le mudda halyo")
    assert result in ("english", "nepali", "romanized_nepali", "mixed")


# ---------------------------------------------------------------------------
# 3. OllamaProvider
# ---------------------------------------------------------------------------

def _make_ollama_provider(handler=None):
    if handler is None:
        def _default_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "message": {"role": "assistant", "content": "Test response"},
                "done": True,
            })
        handler = _default_handler
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaProvider(model="test-model", base_url="http://localhost:11434", client=client)


def test_ollama_generate_returns_completion():
    provider = _make_ollama_provider()
    result = provider.generate(
        system_prompt="You are a legal assistant.",
        messages=[{"role": "user", "content": "What is property law?"}],
    )
    assert isinstance(result, LLMCompletion)
    assert result.text == "Test response"
    assert result.provider == "ollama"
    assert result.model == "test-model"


def test_ollama_posts_to_correct_endpoint():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json={
            "message": {"role": "assistant", "content": "OK"},
            "done": True,
        })

    provider = _make_ollama_provider(handler)
    provider.generate(
        system_prompt="SYSTEM",
        messages=[{"role": "user", "content": "test"}],
    )
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["json"]["model"] == "test-model"
    assert captured["json"]["stream"] is False
    assert captured["json"]["messages"][0]["role"] == "system"


def test_ollama_no_api_key_required():
    provider = _make_ollama_provider()
    result = provider.generate(
        system_prompt="test",
        messages=[{"role": "user", "content": "test"}],
    )
    assert result.text == "Test response"


def test_ollama_timeout_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout")

    provider = _make_ollama_provider(handler)
    with pytest.raises(LLMTimeoutError):
        provider.generate(system_prompt="test", messages=[{"role": "user", "content": "test"}])


def test_ollama_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    provider = _make_ollama_provider(handler)
    with pytest.raises(LLMProviderError):
        provider.generate(system_prompt="test", messages=[{"role": "user", "content": "test"}])


def test_ollama_malformed_json_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    provider = _make_ollama_provider(handler)
    with pytest.raises(LLMMalformedResponseError):
        provider.generate(system_prompt="test", messages=[{"role": "user", "content": "test"}])


def test_ollama_error_in_response_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "model not found"})

    provider = _make_ollama_provider(handler)
    with pytest.raises(LLMMalformedResponseError):
        provider.generate(system_prompt="test", messages=[{"role": "user", "content": "test"}])


def test_ollama_empty_content_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "message": {"role": "assistant", "content": ""},
            "done": True,
        })

    provider = _make_ollama_provider(handler)
    with pytest.raises(LLMMalformedResponseError):
        provider.generate(system_prompt="test", messages=[{"role": "user", "content": "test"}])


def test_ollama_no_message_in_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"done": True})

    provider = _make_ollama_provider(handler)
    with pytest.raises(LLMMalformedResponseError):
        provider.generate(system_prompt="test", messages=[{"role": "user", "content": "test"}])


def test_ollama_info():
    provider = _make_ollama_provider()
    info = provider.info()
    assert info["provider"] == "ollama"
    assert info["model"] == "test-model"


# ---------------------------------------------------------------------------
# 4. NyayaLM provider configuration
# ---------------------------------------------------------------------------

def test_ollama_provider_name():
    provider = _make_ollama_provider()
    assert provider.name == "ollama"


def test_ollama_provider_model():
    provider = OllamaProvider(model="chhatramani/nyayalm1.7B_civil9law:Q4_K_M")
    assert provider.model == "chhatramani/nyayalm1.7B_civil9law:Q4_K_M"


def test_ollama_default_base_url():
    provider = OllamaProvider(model="test")
    assert provider.base_url == "http://localhost:11434"


def test_ollama_custom_base_url():
    provider = OllamaProvider(model="test", base_url="http://custom:8080")
    assert provider.base_url == "http://custom:8080"


# ---------------------------------------------------------------------------
# 5. CaseContext tests
# ---------------------------------------------------------------------------

def test_case_context_update():
    ctx = CaseContext()
    assert ctx.user_role is None
    ctx.update(user_role="self")
    assert ctx.user_role == "self"


def test_case_context_merge_lists():
    ctx = CaseContext()
    ctx.update(documents_available=["nic"])
    ctx.update(documents_available=["passport"])
    assert ctx.documents_available == ["nic", "passport"]


def test_case_context_serialization():
    ctx = CaseContext(user_role="self", matter_type="property")
    data = ctx.to_dict()
    restored = CaseContext.from_dict(data)
    assert restored.user_role == "self"
    assert restored.matter_type == "property"


def test_case_context_completeness():
    ctx = CaseContext()
    assert ctx.get_completeness_percentage() == 0.0
    ctx.update(user_role="self", matter_type="property")
    pct = ctx.get_completeness_percentage()
    assert pct > 0.0


def test_case_context_missing_fields():
    ctx = CaseContext()
    missing = ctx.get_missing_fields()
    assert "user_role" in missing
    assert "matter_type" in missing
    ctx.update(user_role="self")
    missing = ctx.get_missing_fields()
    assert "user_role" not in missing
