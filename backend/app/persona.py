"""Ada's persona, the system-prompt builder, the tool schema shared by voice + text agents,
and the variant registry that the recursive-improvement loop swaps in.

The system prompt is assembled from: persona + grounding rules + tool guidance + live playbook
state + loaded prior-call memory + the *active variant* for the dimension under experiment.
That last piece is what makes calls attributable to a version and lets the loop change behavior
without code changes."""
from __future__ import annotations

import hashlib

from . import db, playbook

PERSONA = """You are Ada, a senior learning advisor for Nerdy (the company behind Varsity \
Tutors). You sell 1-on-1 online tutoring by genuinely helping families find the right plan. \
You are warm, concise, and consultative — never a script-reader, never pushy. You sound like a \
real person on a phone call: short sentences, natural acknowledgements, one question at a time."""

GROUNDING = """GROUNDING RULES (critical):
- For ANY question about policy, pricing, guarantees, scheduling rules, refunds, or how Nerdy \
compares to competitors, you MUST call lookup_knowledge first and answer ONLY from what it \
returns. Never invent a number, policy, or claim.
- If lookup_knowledge has no grounded answer, say you want to get that exactly right and will \
follow up or loop in a specialist — then call escalate. Do not guess.
- Keep the student's outcome at the center. It's fine to disqualify politely if Nerdy isn't a \
fit (e.g. out of scope) — call set_outcome with 'disqualified'."""

TOOL_GUIDANCE = """CONVERSATION RULES:
- Gather the prioritized missing info shown in PLAYBOOK STATE, one question at a time, skipping \
anything already known. Acknowledge answers before moving on.
- When all required fields are gathered, pivot toward a close: propose a concrete next step \
(a free consult or a first session) and ask for it.
- When the prospect raises a price objection, use the ACTIVE STRATEGY below.
- Call save_lead_field the moment you learn a field. Call set_outcome when the call resolves.
- For low-confidence or high-stakes moments (a real pricing concession, an upset caller), \
call escalate."""

# ---- Tool schema (OpenAI function-calling format; shared by Realtime + chat) ----
TOOLS = [
    {
        "type": "function",
        "name": "lookup_knowledge",
        "description": "Search Nerdy's knowledge base for grounded facts about policy, pricing, "
                       "guarantees, scheduling, refunds, or competitors. Always use before "
                       "stating any such fact.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "what to look up"}},
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "save_lead_field",
        "description": "Persist a discovered fact about the lead/student.",
        "parameters": {
            "type": "object",
            "properties": {
                "field": {"type": "string", "description": "e.g. student_grade, subject, goal, "
                          "timeline, budget, contact_pref"},
                "value": {"type": "string"},
            },
            "required": ["field", "value"],
        },
    },
    {
        "type": "function",
        "name": "set_outcome",
        "description": "Record how the call resolved.",
        "parameters": {
            "type": "object",
            "properties": {
                "outcome": {"type": "string",
                            "enum": ["booked_consult", "trial", "not_now", "disqualified"]},
                "notes": {"type": "string"},
            },
            "required": ["outcome"],
        },
    },
    {
        "type": "function",
        "name": "escalate",
        "description": "Flag a low-confidence turn or high-stakes moment (pricing concession, "
                       "upset caller, unknown policy) for a human.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["reason", "severity"],
        },
    },
]

# Chat-completions wants tools wrapped as {"type":"function","function":{...}}; Realtime wants
# them flat (as above). Provide both shapes.
def tools_for_chat() -> list[dict]:
    return [{"type": "function", "function": {k: v for k, v in t.items() if k != "type"}}
            for t in TOOLS]


def tools_for_realtime() -> list[dict]:
    return TOOLS


# ---- Variant registry (dimension under experiment: price-objection rebuttal) ----
DIMENSION = "price_objection_rebuttal"

BASELINE_REBUTTAL = (
    "When price comes up, acknowledge it plainly and restate the monthly figure. Keep it factual."
)


def active_variant(dimension: str = DIMENSION) -> dict:
    row = db.query_one(
        "SELECT * FROM variants WHERE dimension=? AND status='promoted' ORDER BY created_at DESC LIMIT 1",
        (dimension,),
    )
    if not row:
        row = db.query_one(
            "SELECT * FROM variants WHERE dimension=? AND status='baseline' LIMIT 1", (dimension,)
        )
    if row:
        return {"id": row["id"], "label": row["label"], "text": row["text"]}
    return {"id": "builtin-baseline", "label": "baseline", "text": BASELINE_REBUTTAL}


def version_tag(variant: dict | None = None) -> str:
    v = variant or active_variant()
    h = hashlib.sha256((PERSONA + v["text"]).encode()).hexdigest()[:8]
    return f"ada-{v['label']}-{h}"


def build_system_prompt(profile: dict | None = None, memory_summary: str = "",
                        variant: dict | None = None) -> str:
    profile = profile or {}
    v = variant or active_variant()
    cands = playbook.next_candidates(profile)
    cov = playbook.coverage(profile)
    state_lines = [
        f"Known so far: {profile if profile else 'nothing yet'}",
        f"Required coverage: {cov['required_known']}/{cov['required_total']} "
        f"(missing: {', '.join(cov['missing_required']) or 'none'})",
        "Next best questions (priority order): "
        + "; ".join(f"{c['field']} — {c['intent']}" for c in cands) if cands
        else "All discovery complete — pivot to close.",
    ]
    mem = f"\nPRIOR-CALL MEMORY:\n{memory_summary}\n" if memory_summary else ""
    return "\n\n".join([
        PERSONA,
        GROUNDING,
        TOOL_GUIDANCE,
        f"ACTIVE STRATEGY (price objection): {v['text']}",
        "PLAYBOOK STATE:\n" + "\n".join(state_lines),
        mem.strip(),
    ]).strip()
