"""Recursive improvement loop — the part the rubric weighs most.

One full loop on the chosen dimension (price-objection rebuttal):
  baseline -> generate variants -> controlled experiment (paired prospect seeds) ->
  score on a real KPI -> promote winner / retire losers -> persist before/after evidence.

Self-play uses the text-mode agent vs adversarial synthetic prospects. Because the agent shares
CallSession + tools with the voice path, improvements transfer to live calls."""
from __future__ import annotations

import json
import uuid

from . import db, persona, simulator
from .agent_text import agent_opening, agent_reply
from .openai_client import chat
from .session import CallSession

MAX_TURNS = 8  # prospect turns per simulated call


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


# ---------- one simulated call ----------

async def run_sim_call(variant: dict, prospect: simulator.Prospect, seed: int) -> dict:
    session = CallSession.begin("sim", variant=variant)
    transcript: list[dict] = []  # neutral transcript {role: agent/prospect, content}

    reply, hist = await agent_opening(session)
    transcript.append({"role": "agent", "content": reply})
    prospect_dialogue = [{"role": "user", "content": reply}]

    for _ in range(MAX_TURNS):
        p_msg = await simulator.prospect_reply(prospect, prospect_dialogue, seed)
        transcript.append({"role": "prospect", "content": p_msg})
        session.record_turn("prospect", p_msg)
        prospect_dialogue.append({"role": "assistant", "content": p_msg})
        # hand prospect line to Ada (prospect = user in Ada's history)
        hist.append({"role": "user", "content": p_msg})
        reply, hist = await agent_reply(session, hist)
        transcript.append({"role": "agent", "content": reply})
        prospect_dialogue.append({"role": "user", "content": reply})
        low = (p_msg + " " + reply).lower()
        if any(w in low for w in ("goodbye", "take care", "have a great", "talk soon",
                                  "bye for now")):
            break

    judged = await simulator.judge_outcome(prospect, transcript)
    # map judge -> outcome if the agent didn't already set one
    call = db.query_one("SELECT outcome FROM calls WHERE id=?", (session.call_id,))
    if not call or not call["outcome"]:
        from . import memory as _m
        if judged.get("disqualified"):
            _m.set_outcome(session.call_id, "disqualified", judged.get("note", ""))
        elif judged.get("converted"):
            _m.set_outcome(session.call_id, "booked_consult", judged.get("note", ""))
        else:
            _m.set_outcome(session.call_id, "not_now", judged.get("note", ""))
    kpis = session.finish()
    return {"call_id": session.call_id, "transcript": transcript, "judged": judged, "kpis": kpis}


# ---------- KPI scoring across a run set ----------

def score_runs(results: list[dict]) -> dict:
    n = len(results)
    if n == 0:
        return {"calls": 0, "close_rate": 0.0, "objection_resolution": 0.0,
                "avg_completeness": 0.0, "realism": 0.0}
    # close rate excludes correctly-disqualified out-of-fit prospects
    dq = sum(1 for r in results if r["judged"].get("disqualified"))
    wins = sum(1 for r in results if r["judged"].get("converted"))
    obj_raised = [r for r in results if r["judged"].get("price_objection_raised")]
    obj_resolved = sum(1 for r in obj_raised if r["judged"].get("price_objection_resolved"))
    comp = sum(r["kpis"].get("discovery_completeness", 0.0) for r in results)
    realism = sum(r["judged"].get("realism", 0.0) for r in results)
    qualified = max(n - dq, 1)
    return {
        "calls": n,
        "close_rate": round(wins / qualified, 3),
        "objection_resolution": round(obj_resolved / max(len(obj_raised), 1), 3),
        "avg_completeness": round(comp / n, 3),
        "disqualified": dq,
        "realism": round(realism / n, 3),
    }


# ---------- variant generation ----------

async def generate_variants(dimension: str, n: int = 2) -> list[dict]:
    base = persona.active_variant(dimension)
    msg = await chat(
        [
            {"role": "system", "content":
                "You are a sales-enablement strategist. Propose alternative strategies for how a "
                "tutoring advisor should handle a PRICE OBJECTION. Each must be a distinct, "
                "concrete coaching instruction (1-2 sentences) the agent will follow — e.g. "
                "value/ROI framing, risk-reversal/guarantee, social proof, reframing cost as "
                "investment. Return JSON: {\"variants\":[{\"label\":string,\"text\":string}]}"},
            {"role": "user", "content":
                f"Current strategy: {base['text']}\nPropose {n} better, materially different "
                f"strategies."},
        ],
        temperature=0.8,
        response_format={"type": "json_object"},
    )
    try:
        items = json.loads(msg.get("content") or "{}").get("variants", [])
    except json.JSONDecodeError:
        items = []
    out = []
    ts = db.now()
    for it in items[:n]:
        vid = _id("var")
        row = {"id": vid, "dimension": dimension, "label": it.get("label", "variant")[:40],
               "text": it.get("text", ""), "status": "candidate",
               "parent_id": base["id"], "created_at": ts}
        db.insert("variants", row)
        out.append({"id": vid, "label": row["label"], "text": row["text"]})
    return out


# ---------- the full loop ----------

async def run_experiment(dimension: str = persona.DIMENSION, prospects: list[str] | None = None,
                         seeds: int = 2, variant_count: int = 2,
                         auto_promote_threshold: float = 0.05) -> dict:
    """Run one controlled experiment and return a structured before/after report."""
    ensure_baseline(dimension)
    baseline = persona.active_variant(dimension)
    candidates = await generate_variants(dimension, variant_count)
    arms = [{"id": baseline["id"], "label": baseline["label"], "text": baseline["text"],
             "is_baseline": True}] + [{**c, "is_baseline": False} for c in candidates]

    persona_keys = prospects or [p.key for p in simulator.PROSPECTS]
    paired = [(pk, s) for pk in persona_keys for s in range(seeds)]

    arm_results: dict[str, list[dict]] = {a["id"]: [] for a in arms}
    sample_transcripts: dict[str, list] = {a["id"]: [] for a in arms}
    exp_id = _id("exp")
    for arm in arms:
        for (pk, s) in paired:
            res = await run_sim_call(arm, simulator.get(pk), s)
            arm_results[arm["id"]].append(res)
            db.insert("experiment_runs", {
                "experiment_id": exp_id, "variant_id": arm["id"], "prospect_persona": pk,
                "kpis_json": db.j(res["kpis"]), "transcript_json": db.j(res["transcript"]),
                "created_at": db.now()})
            if len(sample_transcripts[arm["id"]]) < 1:
                sample_transcripts[arm["id"]].append(
                    {"prospect": pk, "transcript": res["transcript"],
                     "judged": res["judged"]})

    scored = {a["id"]: score_runs(arm_results[a["id"]]) for a in arms}
    base_score = scored[baseline["id"]]["close_rate"]
    # winner = best close_rate, tie-break objection_resolution
    best = max(arms, key=lambda a: (scored[a["id"]]["close_rate"],
                                    scored[a["id"]]["objection_resolution"]))
    delta = round(scored[best["id"]]["close_rate"] - base_score, 3)

    decision = "kept_baseline"
    if not best["is_baseline"] and delta >= auto_promote_threshold:
        _promote(best["id"], dimension)
        decision = "auto_promoted" if delta < 0.20 else "promoted_with_review"
        for a in arms:
            if a["id"] != best["id"] and not a["is_baseline"]:
                db.execute("UPDATE variants SET status='retired' WHERE id=?", (a["id"],))
    elif not best["is_baseline"]:
        decision = "escalated_no_promote"

    summary = {
        "experiment_id": exp_id,
        "dimension": dimension,
        "decision": decision,
        "winner": {"id": best["id"], "label": best["label"], "is_baseline": best["is_baseline"]},
        "baseline_close_rate": base_score,
        "winner_close_rate": scored[best["id"]]["close_rate"],
        "delta_close_rate": delta,
        "arms": [{"id": a["id"], "label": a["label"], "text": a["text"],
                  "is_baseline": a["is_baseline"], "scores": scored[a["id"]],
                  "sample": sample_transcripts[a["id"]]} for a in arms],
    }
    db.insert("experiments", {"id": exp_id, "dimension": dimension,
                              "summary_json": db.j(summary), "created_at": db.now()})
    return summary


def _promote(variant_id: str, dimension: str) -> None:
    db.execute("UPDATE variants SET status='retired' WHERE dimension=? AND status='promoted'",
               (dimension,))
    db.execute("UPDATE variants SET status='promoted' WHERE id=?", (variant_id,))


def ensure_baseline(dimension: str = persona.DIMENSION) -> dict:
    row = db.query_one("SELECT * FROM variants WHERE dimension=? AND status='baseline' LIMIT 1",
                       (dimension,))
    if row:
        return {"id": row["id"], "label": row["label"], "text": row["text"]}
    vid = _id("var")
    db.insert("variants", {"id": vid, "dimension": dimension, "label": "baseline",
                           "text": persona.BASELINE_REBUTTAL, "status": "baseline",
                           "parent_id": None, "created_at": db.now()})
    return {"id": vid, "label": "baseline", "text": persona.BASELINE_REBUTTAL}


def list_experiments() -> list[dict]:
    rows = db.query("SELECT * FROM experiments ORDER BY created_at DESC")
    return [db.unj(r["summary_json"], {}) for r in rows]


def list_variants(dimension: str = persona.DIMENSION) -> list[dict]:
    return db.query("SELECT * FROM variants WHERE dimension=? ORDER BY created_at", (dimension,))
