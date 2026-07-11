"""
VentureMind AI — IBM watsonx.ai (Granite) Client
=================================================
Uses the current /ml/v1/text/chat endpoint (OpenAI-compatible messages format).

NOTE: /ml/v1/text/generation is deprecated for granite-4-h-small and newer models.
      The chat endpoint is the correct API to use.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import IBMServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Watsonx.ai API version
_API_VERSION = "2023-05-29"


class WatsonXClient:
    """Async client for IBM watsonx.ai text generation via the chat endpoint."""

    def __init__(self) -> None:
        self.base_url = settings.IBM_WATSONX_URL.rstrip("/")
        self.api_key = settings.IBM_WATSONX_API_KEY
        self.project_id = settings.IBM_WATSONX_PROJECT_ID
        self.model_id = settings.IBM_GRANITE_MODEL_ID
        self._iam_token: str | None = None

    # ── IAM Token ─────────────────────────────────────────────────────────────

    async def _get_iam_token(self) -> str:
        """Fetch a short-lived IAM bearer token from IBM Cloud."""
        if self._iam_token:
            return self._iam_token
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://iam.cloud.ibm.com/identity/token",
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self.api_key,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code != 200:
                raise IBMServiceError(
                    "Failed to obtain IAM token",
                    {"status_code": resp.status_code, "detail": resp.text},
                )
            self._iam_token = resp.json()["access_token"]
            return self._iam_token

    # ── Chat Generation (primary method) ──────────────────────────────────────

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,  # absorb any extra kwargs gracefully
    ) -> str:
        """
        Call IBM Granite via the /ml/v1/text/chat endpoint.

        Uses the OpenAI-compatible messages format:
          [ {"role": "system", "content": "..."}, {"role": "user", "content": "..."} ]

        Args:
            system_prompt: The agent's system identity / instructions.
            user_prompt:   The user's request / context data.
            max_new_tokens: Token limit override.
            temperature:    Sampling temperature override.

        Returns:
            The assistant's generated text string.
        """
        token = await self._get_iam_token()

        payload: dict[str, Any] = {
            "model_id": self.model_id,
            "project_id": self.project_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "parameters": {
                "max_new_tokens": max_new_tokens or settings.IBM_GRANITE_MAX_NEW_TOKENS,
                "temperature": temperature or settings.IBM_GRANITE_TEMPERATURE,
            },
        }

        import asyncio
        url = f"{self.base_url}/ml/v1/text/chat?version={_API_VERSION}"
        logger.info(
            "Calling IBM Granite (chat)",
            model=self.model_id,
            system_chars=len(system_prompt),
            user_chars=len(user_prompt),
        )

        max_retries = 4
        backoff = 3.0
        resp = None

        for attempt in range(max_retries + 1):
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
            if resp.status_code == 200:
                break
            if resp.status_code == 429 and attempt < max_retries:
                sleep_time = backoff * (2 ** attempt)
                logger.warning(
                    "Watsonx rate limit hit (429), retrying with backoff...",
                    attempt=attempt + 1,
                    sleep_seconds=sleep_time,
                )
                await asyncio.sleep(sleep_time)
            else:
                break

        if resp.status_code != 200:
            logger.error(
                "Granite chat failed",
                status=resp.status_code,
                body=resp.text[:400],
            )
            raise IBMServiceError(
                "IBM Granite chat generation failed",
                {"status_code": resp.status_code, "detail": resp.text},
            )

        data = resp.json()
        # Chat response format: choices[0].message.content
        generated = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        usage = data.get("usage", {})
        logger.info(
            "Granite chat complete",
            output_chars=len(generated),
            tokens=usage.get("total_tokens", "?"),
        )
        return generated.strip()

    # ── Legacy generate() — kept for any direct callers ───────────────────────

    async def generate(
        self,
        prompt: str,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """
        Compatibility shim: converts a raw prompt string into a chat call.
        Splits on '<|user|>' if present, otherwise treats entire string as user turn.
        """
        if "<|system|>" in prompt and "<|user|>" in prompt:
            # Old Granite instruction format — extract parts
            parts = prompt.split("<|user|>")
            system_part = parts[0].replace("<|system|>", "").strip()
            user_part = parts[1].replace("<|assistant|>", "").strip() if len(parts) > 1 else ""
        else:
            system_part = "You are a helpful AI assistant."
            user_part = prompt.strip()

        return await self.generate_structured(
            system_prompt=system_part,
            user_prompt=user_part,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )


@lru_cache(maxsize=1)
def get_watsonx_client() -> WatsonXClient:
    """Return a singleton WatsonX client (cached)."""
    return WatsonXClient()
