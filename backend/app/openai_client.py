"""Thin async wrappers over the OpenAI REST API (real calls — no mocking).

Used for embeddings (KB), chat completions with tool-calling (text-mode agent, simulator,
variant generation, scoring). The Realtime voice socket is handled separately in realtime.py."""
from __future__ import annotations

from typing import Any

import httpx

from .config import OPENAI_API_KEY, OPENAI_EMBED_MODEL, OPENAI_TEXT_MODEL

_BASE = "https://api.openai.com/v1"
_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}


async def embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(
            f"{_BASE}/embeddings",
            headers=_headers(),
            json={"model": model or OPENAI_EMBED_MODEL, "input": texts},
        )
        r.raise_for_status()
        data = r.json()["data"]
        return [d["embedding"] for d in data]


async def chat(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None,
    temperature: float = 0.6,
    response_format: dict | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Returns the raw `choices[0].message` dict (may contain tool_calls)."""
    body: dict[str, Any] = {
        "model": model or OPENAI_TEXT_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
    if tool_choice:
        body["tool_choice"] = tool_choice
    if response_format:
        body["response_format"] = response_format
    if max_tokens:
        body["max_tokens"] = max_tokens
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(f"{_BASE}/chat/completions", headers=_headers(), json=body)
        if r.status_code >= 400:
            raise RuntimeError(f"OpenAI chat error {r.status_code}: {r.text[:500]}")
        return r.json()["choices"][0]["message"]


async def chat_text(messages: list[dict[str, Any]], **kw) -> str:
    msg = await chat(messages, **kw)
    return (msg.get("content") or "").strip()
