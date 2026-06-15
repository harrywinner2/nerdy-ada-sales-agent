"""Cross-call memory + call/transcript persistence.

A lead is keyed by a stable id (a salted hash of a contact handle, or an explicit id). On call
start we hydrate the lead's profile and a short summary of prior calls; on every learned field
and every turn we persist. This is what lets Ada say "last time you mentioned…"."""
from __future__ import annotations

import uuid

from . import db
from .pii import token_hash


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------- leads ----------

def get_or_create_lead(lead_id: str | None = None, contact: str | None = None,
                       alias: str | None = None) -> dict:
    if lead_id:
        row = db.query_one("SELECT * FROM leads WHERE id=?", (lead_id,))
        if row:
            return row
    if contact:
        ch = token_hash(contact)
        row = db.query_one("SELECT * FROM leads WHERE contact_hash=?", (ch,))
        if row:
            return row
    new_id = lead_id or _id("lead")
    ts = db.now()
    row = {
        "id": new_id,
        "alias": alias or "New caller",
        "contact_hash": token_hash(contact) if contact else None,
        "profile_json": db.j({}),
        "created_at": ts,
        "updated_at": ts,
    }
    db.upsert_lead(row)
    return row


def get_profile(lead_id: str) -> dict:
    row = db.query_one("SELECT profile_json FROM leads WHERE id=?", (lead_id,))
    return db.unj(row["profile_json"], {}) if row else {}


def save_field(lead_id: str, field: str, value) -> dict:
    row = db.query_one("SELECT * FROM leads WHERE id=?", (lead_id,))
    profile = db.unj(row["profile_json"], {}) if row else {}
    profile[field] = value
    db.execute("UPDATE leads SET profile_json=?, updated_at=? WHERE id=?",
               (db.j(profile), db.now(), lead_id))
    return profile


def memory_summary(lead_id: str) -> str:
    """Short, human-readable recap of prior calls for prompt injection."""
    calls = db.query(
        "SELECT outcome, version_tag, started_at FROM calls WHERE lead_id=? AND ended_at IS NOT NULL "
        "ORDER BY started_at DESC LIMIT 3", (lead_id,))
    if not calls:
        return ""
    profile = get_profile(lead_id)
    bits = []
    if profile:
        bits.append("Known about them: " + ", ".join(f"{k}={v}" for k, v in profile.items()))
    bits.append(f"{len(calls)} prior call(s); most recent outcome: {calls[0]['outcome'] or 'unresolved'}.")
    return " ".join(bits)


# ---------- calls / turns / decisions ----------

def start_call(channel: str, version_tag: str, lead_id: str | None = None) -> str:
    cid = _id("call")
    db.insert("calls", {
        "id": cid, "lead_id": lead_id, "channel": channel, "version_tag": version_tag,
        "outcome": None, "outcome_notes": None, "kpis_json": db.j({}),
        "started_at": db.now(), "ended_at": None,
    })
    return cid


def end_call(call_id: str, kpis: dict | None = None) -> None:
    db.execute("UPDATE calls SET ended_at=?, kpis_json=? WHERE id=?",
               (db.now(), db.j(kpis or {}), call_id))


def set_outcome(call_id: str, outcome: str, notes: str = "") -> None:
    db.execute("UPDATE calls SET outcome=?, outcome_notes=? WHERE id=?", (outcome, notes, call_id))


def add_turn(call_id: str, role: str, text: str) -> int:
    row = db.query_one("SELECT COALESCE(MAX(idx),-1) AS m FROM turns WHERE call_id=?", (call_id,))
    idx = (row["m"] if row else -1) + 1
    db.insert("turns", {"call_id": call_id, "idx": idx, "role": role, "text": text, "ts": db.now()})
    return idx


def log_decision(call_id: str, turn_index: int, action: str, candidates: list,
                 confidence: float | None, rationale: str = "") -> None:
    db.insert("decisions", {
        "call_id": call_id, "turn_index": turn_index, "action": action,
        "candidates_json": db.j(candidates), "confidence": confidence,
        "rationale": rationale, "ts": db.now(),
    })


def log_escalation(call_id: str, reason: str, severity: str) -> None:
    db.insert("escalations", {"call_id": call_id, "reason": reason, "severity": severity,
                              "ts": db.now()})


def get_call_bundle(call_id: str) -> dict:
    call = db.query_one("SELECT * FROM calls WHERE id=?", (call_id,))
    if not call:
        return {}
    turns = db.query("SELECT idx, role, text, ts FROM turns WHERE call_id=? ORDER BY idx", (call_id,))
    decisions = db.query("SELECT * FROM decisions WHERE call_id=? ORDER BY turn_index", (call_id,))
    escalations = db.query("SELECT * FROM escalations WHERE call_id=? ORDER BY ts", (call_id,))
    profile = get_profile(call["lead_id"]) if call["lead_id"] else {}
    return {
        "call": {**call, "kpis": db.unj(call["kpis_json"], {})},
        "turns": turns,
        "decisions": [{**d, "candidates": db.unj(d["candidates_json"], [])} for d in decisions],
        "escalations": escalations,
        "profile": profile,
    }
