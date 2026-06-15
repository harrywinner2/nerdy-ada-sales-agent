"""Discovery playbook — the prioritized script of required + leading questions, with dynamic
ordering and skip-when-already-known.

The engine doesn't *speak*; it tells the agent which fields are still missing, ranked, so the
model can phrase the next question naturally and decide whether to keep discovering or pivot to
close. `coverage()` powers the discovery-completeness KPI."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    field: str
    priority: int          # lower = ask sooner
    required: bool
    intent: str            # what the agent is trying to learn (guidance, not a script line)


# Tuned for Nerdy / Varsity Tutors tutoring sales (discovery-to-close).
PLAYBOOK: list[Question] = [
    Question("student_grade", 1, True, "the student's grade level or year"),
    Question("subject", 2, True, "which subject(s) they need help with"),
    Question("goal", 3, True, "the goal — grades, a test, confidence, a deadline"),
    Question("timeline", 4, True, "how soon they want to start / any deadline"),
    Question("current_performance", 5, False, "how the student is doing now / pain points"),
    Question("budget", 6, True, "budget comfort / what they expect to invest"),
    Question("decision_maker", 7, False, "who decides / is anyone else involved"),
    Question("schedule", 8, False, "weekly availability for sessions"),
    Question("prior_tutoring", 9, False, "any past tutoring and how it went"),
    Question("contact_pref", 10, True, "best way + time to follow up"),
]

REQUIRED_FIELDS = [q.field for q in PLAYBOOK if q.required]


def remaining(profile: dict) -> list[Question]:
    """Questions whose field is not yet known, in priority order."""
    known = {k for k, v in (profile or {}).items() if v not in (None, "", [])}
    return sorted([q for q in PLAYBOOK if q.field not in known], key=lambda q: q.priority)


def next_candidates(profile: dict, n: int = 3) -> list[dict]:
    return [{"field": q.field, "intent": q.intent, "required": q.required}
            for q in remaining(profile)[:n]]


def coverage(profile: dict) -> dict:
    known = {k for k, v in (profile or {}).items() if v not in (None, "", [])}
    req_known = [f for f in REQUIRED_FIELDS if f in known]
    return {
        "required_total": len(REQUIRED_FIELDS),
        "required_known": len(req_known),
        "completeness": round(len(req_known) / len(REQUIRED_FIELDS), 3),
        "missing_required": [f for f in REQUIRED_FIELDS if f not in known],
    }


def ready_to_close(profile: dict) -> bool:
    """Pivot heuristic: all required discovery fields gathered."""
    return coverage(profile)["completeness"] >= 1.0
