"""KPI computation — the sales metrics the PRD wants tracked and attributed by version.

These are computed from the observability store (calls/turns/decisions/escalations), so the
same definitions apply to real calls and simulated experiment runs. Honest KPIs: close rate
counts only booked_consult/trial; disqualified is NOT a loss (politely letting a non-fit go is
correct behavior)."""
from __future__ import annotations

from . import db, playbook

WIN_OUTCOMES = {"booked_consult", "trial"}


def call_kpis(bundle: dict) -> dict:
    """Per-call KPIs from a get_call_bundle() result."""
    call = bundle["call"]
    turns = bundle["turns"]
    decisions = bundle["decisions"]
    profile = bundle.get("profile", {})
    cov = playbook.coverage(profile)
    objection_turns = [d for d in decisions if d["action"] in ("answer", "pivot_close")]
    grounded = [d for d in decisions if d.get("rationale", "").startswith("grounded")]
    factual = [d for d in decisions if "ground" in (d.get("rationale") or "")]
    return {
        "outcome": call.get("outcome"),
        "won": call.get("outcome") in WIN_OUTCOMES,
        "disqualified": call.get("outcome") == "disqualified",
        "discovery_completeness": cov["completeness"],
        "turns": len([t for t in turns if t["role"] == "prospect"]),
        "escalations": len(bundle.get("escalations", [])),
        "decisions": len(decisions),
        "grounded_answers": len(grounded) or len(factual),
    }


def aggregate(version_tag: str | None = None) -> dict:
    """Top-line KPIs across calls, optionally filtered to a version."""
    where = "WHERE ended_at IS NOT NULL"
    params: tuple = ()
    if version_tag:
        where += " AND version_tag=?"
        params = (version_tag,)
    calls = db.query(f"SELECT * FROM calls {where}", params)
    n = len(calls)
    if n == 0:
        return {"calls": 0, "close_rate": 0.0, "avg_completeness": 0.0,
                "disqualified_rate": 0.0, "escalation_rate": 0.0, "avg_turns": 0.0}
    wins = sum(1 for c in calls if c["outcome"] in WIN_OUTCOMES)
    dq = sum(1 for c in calls if c["outcome"] == "disqualified")
    comp, turns_tot, esc_tot = 0.0, 0, 0
    for c in calls:
        k = db.unj(c["kpis_json"], {})
        comp += k.get("discovery_completeness", 0.0)
        turns_tot += k.get("turns", 0)
        esc_tot += k.get("escalations", 0)
    # close rate denominator excludes disqualified (those were correctly not-a-fit)
    qualified = max(n - dq, 1)
    return {
        "calls": n,
        "close_rate": round(wins / qualified, 3),
        "avg_completeness": round(comp / n, 3),
        "disqualified_rate": round(dq / n, 3),
        "escalation_rate": round(esc_tot / n, 3),
        "avg_turns": round(turns_tot / n, 2),
    }


def versions() -> list[dict]:
    rows = db.query(
        "SELECT version_tag, COUNT(*) AS calls FROM calls WHERE ended_at IS NOT NULL "
        "GROUP BY version_tag ORDER BY calls DESC")
    out = []
    for r in rows:
        agg = aggregate(r["version_tag"])
        out.append({"version_tag": r["version_tag"], **agg})
    return out
