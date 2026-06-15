"""SQLite persistence — memory + full observability store.

One file-backed DB powers everything: leads (cross-call memory), calls, turns (transcripts),
decisions (the decision log the PRD wants surfaced), escalations, the KB, and the
recursive-improvement tables (variants / experiments / runs). Zero-ops, portable to Postgres."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from .config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY,
  alias TEXT,
  contact_hash TEXT,
  profile_json TEXT NOT NULL DEFAULT '{}',
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS calls (
  id TEXT PRIMARY KEY,
  lead_id TEXT,
  channel TEXT NOT NULL,            -- web | phone | sim
  version_tag TEXT NOT NULL,
  outcome TEXT,                     -- booked_consult | trial | not_now | disqualified | null
  outcome_notes TEXT,
  kpis_json TEXT NOT NULL DEFAULT '{}',
  started_at REAL NOT NULL,
  ended_at REAL
);
CREATE TABLE IF NOT EXISTS turns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id TEXT NOT NULL,
  idx INTEGER NOT NULL,
  role TEXT NOT NULL,               -- agent | prospect
  text TEXT NOT NULL,               -- PII-redacted
  ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id TEXT NOT NULL,
  turn_index INTEGER NOT NULL,
  action TEXT NOT NULL,             -- ask | answer | pivot_close | escalate | disqualify
  candidates_json TEXT NOT NULL DEFAULT '[]',
  confidence REAL,
  rationale TEXT,
  ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS escalations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  severity TEXT NOT NULL,
  ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS kb_docs (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  category TEXT NOT NULL,           -- policy | objection | competitive | pricing | product
  content TEXT NOT NULL,
  embedding BLOB
);
CREATE TABLE IF NOT EXISTS variants (
  id TEXT PRIMARY KEY,
  dimension TEXT NOT NULL,          -- e.g. price_objection_rebuttal
  label TEXT NOT NULL,
  text TEXT NOT NULL,
  status TEXT NOT NULL,             -- baseline | candidate | promoted | retired
  parent_id TEXT,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS experiments (
  id TEXT PRIMARY KEY,
  dimension TEXT NOT NULL,
  summary_json TEXT NOT NULL DEFAULT '{}',
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS experiment_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  experiment_id TEXT NOT NULL,
  variant_id TEXT NOT NULL,
  prospect_persona TEXT NOT NULL,
  kpis_json TEXT NOT NULL DEFAULT '{}',
  transcript_json TEXT NOT NULL DEFAULT '[]',
  created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_turns_call ON turns(call_id);
CREATE INDEX IF NOT EXISTS idx_decisions_call ON decisions(call_id);
CREATE INDEX IF NOT EXISTS idx_runs_exp ON experiment_runs(experiment_id);
"""


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db() -> None:
    with _conn() as c:
        c.executescript(_SCHEMA)


def now() -> float:
    return time.time()


# ---------- generic helpers ----------

def execute(sql: str, params: tuple = ()) -> None:
    with _conn() as c:
        c.execute(sql, params)


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    with _conn() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def query_one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def insert(table: str, row: dict[str, Any]) -> None:
    cols = ",".join(row.keys())
    ph = ",".join("?" for _ in row)
    with _conn() as c:
        c.execute(f"INSERT INTO {table} ({cols}) VALUES ({ph})", tuple(row.values()))


def upsert_lead(row: dict[str, Any]) -> None:
    with _conn() as c:
        c.execute(
            """INSERT INTO leads (id, alias, contact_hash, profile_json, created_at, updated_at)
               VALUES (:id,:alias,:contact_hash,:profile_json,:created_at,:updated_at)
               ON CONFLICT(id) DO UPDATE SET
                 alias=excluded.alias, contact_hash=excluded.contact_hash,
                 profile_json=excluded.profile_json, updated_at=excluded.updated_at""",
            row,
        )


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def unj(text: str | None, default: Any = None) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default
