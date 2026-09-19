"""Unit tests for the LLM provider abstraction.

Everything runs against ``httpx.MockTransport``, so no network call and no API
key are ever needed. The tests pin the provider contract: request shape, typed
failures for every failure mode, and the guarantee that a key never leaks into a
message, a log line or a response.
"""

import json

import httpx
import pytest

from app.services.llm import (
    DEFAULT_BASE_URLS,
    LLMError,
    LLMMalformedResponseError,
    LLMNotConfiguredError,
    LLMProviderError,
    LLMTimeoutError,
    OpenAICompatibleProvider,
    get_llm_provider,
    reset_llm_provider_cache,
)

SECRET = "sk-secret-value-that-must-not-leak"

COMPLETION = {
    "choices": [{"message": {"role": "assistant", "content": "ग्राउन्डेड उत्तर।"}}]
}


def _provider(handler, **overrides):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    kwargs = {
        "api_key": SECRET,
        "model": "test-model",
        "provider_name": "groq",
        "client": client,
    }
    kwargs.update(overrides)
    return OpenAICompatibleProvider(**kwargs)


def _ok_handler(captured):
    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json=COMPLETION)

    return handler


# --------------------------------------------------------------------------- #
# Happy path / request shape
# --------------------------------------------------------------------------- #

def test_generate_returns_the_completion_text():
    captured = {}
    completion = _provider(_ok_handler(captured)).generate(
        system_prompt="SYSTEM", messages=[{"role": "user", "content": "hi"}]
    )

    assert completion.text == "ग्राउन्डेड उत्तर।"
    assert completion.provider == "groq"
    assert completion.model == "test-model"


def test_generate_posts_to_the_chat_completions_endpoint():
    captured = {}
    _provider(_ok_handler(captured)).generate(
        system_prompt="SYSTEM", messages=[{"role": "user", "content": "hi"}]
    )

    assert captured["url"] == f"{DEFAULT_BASE_URLS['groq']}/chat/completions"
    assert captured["headers"]["authorization"] == f"Bearer {SECRET}"


def test_system_prompt_is_the_first_message():
    captured = {}
    _provider(_ok_handler(captured)).generate(
        system_prompt="STRICT RULES",
        messages=[
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "second"},
        ],
    )

    messages = captured["json"]["messages"]
    assert messages[0] == {"role": "system", "content": "STRICT RULES"}
    assert [m["role"] for m in messages[1:]] == ["user", "assistant", "user"]
    assert messages[-1]["content"] == "second"
    assert captured["json"]["model"] == "test-model"
    assert captured["json"]["temperature"] == 0.0


def test_base_url_override_is_used():
    captured = {}
    _provider(
        _ok_handler(captured),
        provider_name="openai",
        base_url="https://llm.internal.example/v1/",
    ).generate(system_prompt="s", messages=[{"role": "user", "content": "q"}])

    assert captured["url"] == "https://llm.internal.example/v1/chat/completions"


def test_completion_does_not_expose_the_api_key():
    completion = _provider(_ok_handler({})).generate(
        system_prompt="s", messages=[{"role": "user", "content": "q"}]
    )
    assert SECRET not in repr(completion)
    assert SECRET not in str(completion.text)


# --------------------------------------------------------------------------- #
# Failure modes
# --------------------------------------------------------------------------- #

def _raise(exc):
    def handler(request: httpx.Request) -> httpx.Response:
        raise exc

    return handler


def test_timeout_raises_a_typed_error():
    provider = _provider(_raise(httpx.ReadTimeout("too slow")))
    with pytest.raises(LLMTimeoutError) as excinfo:
        provider.generate(system_prompt="s", messages=[{"role": "user", "content": "q"}])

    assert excinfo.value.kind == "timeout"
    assert SECRET not in str(excinfo.value)


def test_transport_failure_raises_a_provider_error():
    provider = _provider(_raise(httpx.ConnectError("no route")))
    with pytest.raises(LLMProviderError) as excinfo:
        provider.generate(system_prompt="s", messages=[{"role": "user", "content": "q"}])

    assert excinfo.value.kind == "provider_error"
    assert SECRET not in str(excinfo.value)


@pytest.mark.parametrize("status", [400, 401, 429, 500, 503])
def test_http_error_status_raises_a_provider_error(status):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text="nope")

    provider = _provider(handler)
    with pytest.raises(LLMProviderError) as excinfo:
        provider.generate(system_prompt="s", messages=[{"role": "user", "content": "q"}])

    assert excinfo.value.status_code == status
    assert str(status) in str(excinfo.value)
    assert SECRET not in str(excinfo.value)


def test_non_json_response_raises_malformed():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    with pytest.raises(LLMMalformedResponseError):
        _provider(handler).generate(
            system_prompt="s", messages=[{"role": "user", "content": "q"}]
        )


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"choices": []},
        {"choices": [{}]},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": ""}}]},
        {"choices": [{"message": {"content": "   "}}]},
        {"choices": "not-a-list"},
        {"error": {"message": "bad request"}},
    ],
)
def test_malformed_payloads_raise_malformed(body):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    with pytest.raises(LLMMalformedResponseError):
        _provider(handler).generate(
            system_prompt="s", messages=[{"role": "user", "content": "q"}]
        )


def test_all_errors_share_the_base_class():
    for exc in (
        LLMNotConfiguredError("x"),
        LLMTimeoutError("x"),
        LLMProviderError("x"),
        LLMMalformedResponseError("x"),
    ):
        assert isinstance(exc, LLMError)
        assert isinstance(exc.kind, str) and exc.kind


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

def test_provider_requires_an_api_key():
    with pytest.raises(LLMNotConfiguredError):
        OpenAICompatibleProvider(api_key="", model="m", provider_name="groq")
    with pytest.raises(LLMNotConfiguredError):
        OpenAICompatibleProvider(api_key="   ", model="m", provider_name="groq")


def test_unknown_provider_without_base_url_is_not_configured():
    with pytest.raises(LLMNotConfiguredError):
        OpenAICompatibleProvider(api_key=SECRET, model="m", provider_name="mystery")


class _Settings:
    """Minimal stand-in for the app settings."""

    def __init__(self, **overrides):
        self.llm_provider = "groq"
        self.llm_api_key = ""
        self.llm_model = "llama-3.3-70b-versatile"
        self.llm_base_url = ""
        self.llm_timeout_seconds = 30.0
        for key, value in overrides.items():
            setattr(self, key, value)

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key.strip())


def test_get_llm_provider_returns_none_without_a_key():
    assert get_llm_provider(settings_obj=_Settings(llm_api_key="")) is None


def test_get_llm_provider_builds_an_openai_compatible_provider():
    provider = get_llm_provider(
        settings_obj=_Settings(llm_api_key=SECRET, llm_model="m1")
    )
    assert provider is not None
    assert provider.model == "m1"
    assert SECRET not in repr(provider.info())
    provider.close()


def test_get_llm_provider_falls_back_to_groq_for_an_unknown_provider():
    provider = get_llm_provider(
        settings_obj=_Settings(llm_api_key=SECRET, llm_provider="made-up")
    )
    assert provider is not None and provider.name == "groq"
    provider.close()


def test_get_llm_provider_honours_an_explicit_base_url_for_a_custom_provider():
    provider = get_llm_provider(
        settings_obj=_Settings(
            llm_api_key=SECRET,
            llm_provider="self-hosted",
            llm_base_url="https://llm.internal.example/v1",
        )
    )
    assert provider is not None
    assert provider.base_url == "https://llm.internal.example/v1"
    provider.close()


def test_explicit_client_is_never_cached_or_closed_by_the_provider():
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=COMPLETION)))
    provider = OpenAICompatibleProvider(
        api_key=SECRET, model="m", provider_name="groq", client=client
    )
    provider.close()
    # A caller-supplied client stays open (the caller owns it).
    assert not client.is_closed
    client.close()


def test_default_provider_is_cached_and_resettable():
    """The process-wide provider is built once and rebuilt after a reset.

    Environment-independent: whether or not a key is configured, repeated calls
    must return the same object and a reset must drop it.
    """
    reset_llm_provider_cache()
    first = get_llm_provider()
    assert get_llm_provider() is first
    assert first is None or isinstance(first, OpenAICompatibleProvider)

    reset_llm_provider_cache()
    assert get_llm_provider() is not first
    reset_llm_provider_cache()


def test_configured_provider_is_usable_without_exposing_the_key():
    """If the environment does configure a provider, its public info is safe."""
    provider = get_llm_provider()
    if provider is None:
        pytest.skip("no LLM credentials configured in this environment")

    info = provider.info()
    assert set(info) == {"provider", "model"}
    assert not any("key" in k.lower() or "token" in k.lower() for k in info)
    reset_llm_provider_cache()
