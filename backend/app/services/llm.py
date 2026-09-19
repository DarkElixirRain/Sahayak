"""LLM provider abstraction - Phase 5 grounded generation.

Design:

    LLMProvider (abstract)
        └── OpenAICompatibleProvider   # Groq, OpenAI, or any compatible proxy
                └── driven by configuration: LLM_PROVIDER / LLM_API_KEY /
                    LLM_MODEL / LLM_BASE_URL / LLM_TIMEOUT_SECONDS

The project's earlier convention used ``GROQ_API_KEY``; that name still works as
a fallback and ``groq`` remains the default provider, so no existing deployment
needs to change anything to keep working.

Guarantees:

* an API key is **never** logged, returned, or included in an error message
* every failure mode raises a typed :class:`LLMError`, so callers can degrade
  gracefully instead of returning a stack trace or a fabricated answer
* transport failures, timeouts, HTTP errors, non-JSON bodies and malformed
  payloads are all distinguished
* constructing a provider without configuration raises only from the
  constructor; :func:`get_llm_provider` returns ``None`` instead so the API
  stays usable with generation disabled
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import httpx

from app.core.config import Settings, settings

logger = logging.getLogger("app.services.llm")

# OpenAI-compatible chat-completions endpoints.
DEFAULT_BASE_URLS: Mapping[str, str] = {
    "groq": "https://api.groq.com/openai/v1",
    "openai": "https://api.openai.com/v1",
}

DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 900


class LLMError(Exception):
    """Base class for LLM failures.

    ``kind`` is a stable, client-safe discriminator that never contains
    provider internals or credentials.
    """

    kind = "llm_error"

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class LLMNotConfiguredError(LLMError):
    """No API key / unusable provider configuration."""

    kind = "not_configured"


class LLMTimeoutError(LLMError):
    """The provider did not answer within the configured timeout."""

    kind = "timeout"


class LLMProviderError(LLMError):
    """The provider refused the request, or the network failed."""

    kind = "provider_error"


class LLMMalformedResponseError(LLMError):
    """The provider answered, but not with a usable completion."""

    kind = "malformed_response"


@dataclass(frozen=True)
class LLMCompletion:
    """A validated completion returned by a provider."""

    text: str
    provider: str
    model: str


class LLMProvider(ABC):
    """Interface every LLM backend must implement."""

    name: str
    model: str

    @abstractmethod
    def generate(
        self,
        *,
        system_prompt: str,
        messages: Sequence[Mapping[str, str]],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> LLMCompletion:
        """Generate a completion for ``messages`` under ``system_prompt``."""

    def info(self) -> dict[str, str]:
        """Public, non-secret description of this provider."""
        return {"provider": self.name, "model": self.model}


def _extract_message_text(data: Any) -> str:
    """Pull the assistant text out of an OpenAI-compatible response body."""
    if not isinstance(data, dict):
        raise LLMMalformedResponseError("LLM provider returned an unexpected body")

    if isinstance(data.get("error"), dict):
        # A 200 response carrying an error object is still a failure.
        raise LLMMalformedResponseError("LLM provider returned an error object")

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMMalformedResponseError("LLM provider returned no choices")

    first = choices[0]
    message = first.get("message") if isinstance(first, dict) else None
    content = message.get("content") if isinstance(message, dict) else None

    if not isinstance(content, str) or not content.strip():
        raise LLMMalformedResponseError("LLM provider returned an empty completion")

    return content


class OpenAICompatibleProvider(LLMProvider):
    """Provider for any OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        provider_name: str = "groq",
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise LLMNotConfiguredError(
                "LLM provider is not configured: no API key", status_code=None
            )

        resolved_base = (base_url or DEFAULT_BASE_URLS.get(provider_name, "")).strip()
        if not resolved_base:
            raise LLMNotConfiguredError(
                f"LLM provider '{provider_name}' has no known endpoint; "
                "set LLM_BASE_URL"
            )

        self.name = provider_name
        self.model = model
        self.base_url = resolved_base.rstrip("/")
        self._api_key = api_key.strip()
        self._timeout = timeout
        self._client = client if client is not None else httpx.Client(timeout=timeout)
        self._owns_client = client is None

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def close(self) -> None:
        """Release the HTTP client if this provider created it."""
        if self._owns_client:
            self._client.close()

    def generate(
        self,
        *,
        system_prompt: str,
        messages: Sequence[Mapping[str, str]],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> LLMCompletion:
        """Call the provider and return a validated completion.

        Raises:
            LLMTimeoutError: the request exceeded the configured timeout.
            LLMProviderError: network failure or a non-2xx provider response.
            LLMMalformedResponseError: the body was not a usable completion.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *[
                    {"role": str(m.get("role", "user")),
                     "content": str(m.get("content", ""))}
                    for m in messages
                ],
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self._client.post(
                self.endpoint, json=payload, headers=headers, timeout=self._timeout
            )
        except httpx.TimeoutException as exc:
            # Deliberately does not include str(exc): it can echo request detail.
            raise LLMTimeoutError(
                f"LLM request timed out after {self._timeout:g}s"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(
                f"LLM request failed ({type(exc).__name__})"
            ) from exc

        if response.status_code >= 400:
            raise LLMProviderError(
                f"LLM provider returned HTTP {response.status_code}",
                status_code=response.status_code,
            )

        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMMalformedResponseError(
                "LLM provider returned a non-JSON response"
            ) from exc

        text = _extract_message_text(data)
        return LLMCompletion(text=text.strip(), provider=self.name, model=self.model)


# Process-wide cache so a long-running server reuses one HTTP client (and its
# connection pool) instead of building one per request. Only successful builds
# are cached, and tests can reset it.
_provider_cache: LLMProvider | None = None
_provider_cache_ready = False


def reset_llm_provider_cache() -> None:
    """Drop the cached provider (used by tests and after config changes)."""
    global _provider_cache, _provider_cache_ready
    if _provider_cache is not None:
        _provider_cache.close()
    _provider_cache = None
    _provider_cache_ready = False


def _build_provider(
    active: Settings, client: httpx.Client | None
) -> LLMProvider | None:
    """Construct a provider, or return ``None`` when unusable."""
    if not active.llm_configured:
        logger.info("LLM provider not configured: grounded generation disabled")
        return None

    provider_name = (active.llm_provider or "groq").strip().lower()
    if provider_name not in DEFAULT_BASE_URLS and not active.llm_base_url:
        logger.warning(
            "Unknown LLM_PROVIDER %r with no LLM_BASE_URL; using 'groq'",
            provider_name,
        )
        provider_name = "groq"

    try:
        return OpenAICompatibleProvider(
            api_key=active.llm_api_key,
            model=active.llm_model,
            base_url=active.llm_base_url or None,
            provider_name=provider_name,
            timeout=active.llm_timeout_seconds,
            client=client,
        )
    except LLMNotConfiguredError as exc:
        logger.warning("LLM provider unavailable: %s", exc)
        return None


def get_llm_provider(
    *,
    settings_obj: Settings | None = None,
    client: httpx.Client | None = None,
) -> LLMProvider | None:
    """Return the configured provider, or ``None`` when generation is disabled.

    Returns ``None`` (never raises) when no API key is configured, so a
    deployment without LLM credentials still serves retrieval and returns a
    controlled "generation unavailable" response.

    The default (no explicit settings/client) result is cached process-wide so
    the HTTP connection pool is reused across requests.
    """
    global _provider_cache, _provider_cache_ready

    if settings_obj is not None or client is not None:
        return _build_provider(settings_obj or settings, client)

    if not _provider_cache_ready:
        _provider_cache = _build_provider(settings, None)
        _provider_cache_ready = True
    return _provider_cache
