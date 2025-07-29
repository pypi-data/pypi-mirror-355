# deepseek_chat/client.py
"""Lightweight synchronous wrapper around DeepSeek /chat/completions.

This module is **step 1 (Milestone M1)** of the planned implementation:
• Pull API‑Key & base URL from environment but allow explicit override.
• Provide a `DeepSeekClient.chat()` helper that handles retry & basic
  error mapping.  Down‑stream service layer will build on this.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
from requests import Response, Session, exceptions as req_exc

__all__ = [
    "DeepSeekClient",
    "DeepSeekClientError",
    "DeepSeekRateLimitError",
    "DeepSeekServerError",
]


class DeepSeekClientError(RuntimeError):
    """Base class for all client‑side errors."""


class DeepSeekRateLimitError(DeepSeekClientError):
    """Raised on HTTP 429 or when ``error.code == 'rate_limit_exceeded'``."""


class DeepSeekServerError(DeepSeekClientError):
    """Raised on 5xx responses that are not covered by a more specific error."""


class DeepSeekClient:
    """Minimal DeepSeek chat‑completion client (sync).

    Parameters
    ----------
    api_key
        If *None*, fall back to ``DEEPSEEK_API_KEY`` env var.
    base_url
        If *None*, default to ``https://api.deepseek.com`` or
        env var ``DEEPSEEK_BASE_URL``.
    model
        Default model name when caller does not specify.
    timeout
        Per‑request timeout (seconds).
    max_retries
        Automatic retries on 429/5xx (exponential back‑off, capped at
        *max_retries* attempts **in addition to** the first try).
    backoff_factor
        The initial sleep seconds. Each retry sleeps
        ``backoff_factor * 2 ** (retry_count - 1)``.
    """

    _DEFAULT_BASE_URL = "https://api.deepseek.com"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        backoff_factor: float = 0.8,
        session: Optional[Session] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise DeepSeekClientError("`api_key` missing (env DEEPSEEK_API_KEY not set)")

        self.base_url = (
            base_url
            or os.getenv("DEEPSEEK_BASE_URL")
            or self._DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        # Allow caller to inject a custom requests.Session (e.g. for proxy)
        self._session: Session = session or requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "deepseek-chat-python/0.1",
            }
        )

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def chat(
        self,
        *,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        stream: bool = False,
        **extra: Any,
    ) -> Dict[str, Any]:
        """Call `/chat/completions` and return JSON.

        Caller may pass any additional parameters accepted by DeepSeek
        (e.g. temperature, top_p, max_tokens). Unknown kwargs are
        forwarded as‑is.
        """
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            **extra,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if stream:
            payload["stream"] = True
        endpoint = f"{self.base_url}/chat/completions"
        return self._request_json("POST", endpoint, payload)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _request_json(self, method: str, url: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        retries = 0
        last_exc: Optional[Exception] = None
        while retries <= self.max_retries:
            try:
                resp: Response = self._session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    json=json_body,
                )
                if resp.status_code == 200:
                    return resp.json()
                self._handle_http_error(resp)
            except (DeepSeekRateLimitError, DeepSeekServerError, req_exc.Timeout) as exc:
                last_exc = exc
                retries += 1
                if retries > self.max_retries:
                    break
                sleep_s = self.backoff_factor * (2 ** (retries - 1))
                time.sleep(sleep_s)
            except req_exc.RequestException as exc:
                # Non‑retryable network error
                raise DeepSeekClientError(str(exc)) from exc
        # Retries exhausted
        assert last_exc is not None  # for type checker
        raise last_exc

    def _handle_http_error(self, resp: Response) -> None:
        status = resp.status_code
        try:
            data = resp.json()
        except ValueError:
            data = {}
        msg = data.get("error", {}).get("message") or resp.text
        if status == 429:
            raise DeepSeekRateLimitError(msg)
        if 500 <= status < 600:
            raise DeepSeekServerError(msg)
        raise DeepSeekClientError(f"HTTP {status}: {msg}")
