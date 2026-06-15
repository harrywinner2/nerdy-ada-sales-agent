"""PII substitution. Transcripts are stored PII-free by construction (PRD requirement).

We detect names, phone numbers, and emails and replace them with stable per-call tokens
(<NAME_1>, <PHONE_1>, <EMAIL_1>). The mapping from token -> raw value lives only in process
memory for the duration of a call (the Redactor instance) and is never persisted. A salted
hash is what we keep if we ever need to correlate without revealing the value."""
from __future__ import annotations

import hashlib
import re

from .config import PII_SALT

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# North-American style numbers, lenient on separators.
_PHONE = re.compile(r"(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
# Capitalized first+last name pairs (heuristic — good enough for synthetic + demo data).
_NAME = re.compile(r"\b([A-Z][a-z]{1,15})\s([A-Z][a-z]{1,15})\b")


def token_hash(value: str) -> str:
    return hashlib.sha256((PII_SALT + value.lower()).encode()).hexdigest()[:16]


class Redactor:
    """Stateful per-call redactor; reuse one instance for a whole call so the same person
    keeps the same token across turns."""

    def __init__(self) -> None:
        self._map: dict[str, str] = {}
        self._counts = {"NAME": 0, "PHONE": 0, "EMAIL": 0}

    def _token(self, kind: str, raw: str) -> str:
        if raw in self._map:
            return self._map[raw]
        self._counts[kind] += 1
        tok = f"<{kind}_{self._counts[kind]}>"
        self._map[raw] = tok
        return tok

    def redact(self, text: str) -> str:
        if not text:
            return text
        text = _EMAIL.sub(lambda m: self._token("EMAIL", m.group(0)), text)
        text = _PHONE.sub(lambda m: self._token("PHONE", m.group(0)), text)
        text = _NAME.sub(lambda m: self._token("NAME", m.group(0)), text)
        return text

    @property
    def alias_map(self) -> dict[str, str]:
        # token -> salted hash (safe to inspect; never the raw value)
        return {tok: token_hash(raw) for raw, tok in self._map.items()}


def redact_once(text: str) -> str:
    """Stateless one-shot redaction for ad-hoc strings."""
    return Redactor().redact(text)
