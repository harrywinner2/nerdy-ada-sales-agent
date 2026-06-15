"""Central configuration. All secrets come from the environment (untracked .env in dev,
Railway secret store in prod). Nothing secret is ever hard-coded here."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level above backend/) if present. Safe in prod (no-op).
_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")

# ---- OpenAI ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_REALTIME_MODEL = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime")
# Cheaper/faster text model for self-play, variant generation, scoring, decision rationale.
OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OPENAI_VOICE = os.getenv("OPENAI_VOICE", "marin")  # warm female voice for Ada

# ---- Twilio (phone channel; optional — web channel works without it) ----
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# ---- App ----
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")  # set to https Railway URL for Twilio webhooks
DB_PATH = os.getenv("DB_PATH", str(_ROOT / "data" / "ada.db"))
PII_SALT = os.getenv("PII_SALT", "ada-dev-salt-rotate-me")
PORT = int(os.getenv("PORT", "8000"))

OPENAI_REALTIME_URL = f"wss://api.openai.com/v1/realtime?model={OPENAI_REALTIME_MODEL}"


def have_openai() -> bool:
    return bool(OPENAI_API_KEY)


def have_twilio() -> bool:
    return bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)
