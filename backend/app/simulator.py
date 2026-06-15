"""Synthetic prospects for self-play. These are deliberately NOT obedient — each has hidden
goals, real objections, and walk-away conditions, so a win has to be earned (this is exactly
the failure mode the PRD rubric calls out: a swarm of agreeable leads inflating win rate).

Each prospect is an LLM persona that replies in character given the dialogue so far. A separate
judge extracts whether they were converted, disqualified, or walked, plus whether their price
objection was actually resolved (for the objection-resolution KPI)."""
from __future__ import annotations

import json
from dataclasses import dataclass

from .openai_client import chat, chat_text


@dataclass(frozen=True)
class Prospect:
    key: str
    label: str
    brief: str
    fit: str          # "in_icp" or "out_of_icp"


PROSPECTS: list[Prospect] = [
    Prospect("budget_skeptic", "Budget Skeptic",
             "Parent of an 8th grader struggling in algebra. Genuinely interested but sticker-"
             "shocked. You push hard on price at least twice, ask if there's anything cheaper, "
             "and compare to a $25/hr local tutor. You can be won by a clear value/ROI or a "
             "low-risk first step, but NOT by pressure. If the advisor caves to a big random "
             "discount, you get suspicious.", "in_icp"),
    Prospect("fence_sitter", "Fence Sitter",
             "Parent of a 10th grader. Polite but non-committal. You hedge ('let me think about "
             "it', 'I should ask my partner'), give short answers, and stall on booking. You "
             "convert only if the advisor creates a concrete, low-friction next step and a mild "
             "reason to act now. You dislike being rushed.", "in_icp"),
    Prospect("comparison_shopper", "Comparison Shopper",
             "Parent shopping around. You name-drop competitors (a big-box tutoring chain and a "
             "free app) and ask why Nerdy is better. You want specifics, not fluff. You convert "
             "if the advisor gives grounded, credible differentiation; you disengage if it's "
             "vague or salesy.", "in_icp"),
    Prospect("disqualifier", "Disqualifier (out of fit)",
             "You're calling about test prep for a professional certification exam that Nerdy "
             "tutoring doesn't really cover, OR you want a guarantee of a specific score. A good "
             "advisor should recognize you're not a fit and politely disqualify rather than "
             "force a sale. You get annoyed if oversold.", "out_of_icp"),
    Prospect("ready_buyer", "Ready Buyer",
             "Parent of a 9th grader with a geometry test in two weeks. Motivated and fairly "
             "decisive, but you still want to know the price and how scheduling works before "
             "committing. You convert quickly if the advisor is competent and clear.", "in_icp"),
]


def get(key: str) -> Prospect:
    for p in PROSPECTS:
        if p.key == key:
            return p
    raise KeyError(key)


def _system(p: Prospect, seed: int) -> str:
    return (
        f"You are a synthetic sales PROSPECT in a roleplay to stress-test a tutoring sales "
        f"agent. Stay fully in character. Persona: {p.label}. {p.brief}\n"
        f"Rules: Reply ONLY as the prospect, 1-3 sentences, natural and human. Never break "
        f"character or mention you are an AI. Raise your objection(s) when relevant. Do not "
        f"volunteer everything at once. Vary your wording (seed {seed}). End the call naturally "
        f"if you decide to buy, to disqualify yourself, or to walk away."
    )


async def prospect_reply(p: Prospect, dialogue: list[dict], seed: int) -> str:
    """dialogue from the prospect's POV: agent lines = user, prospect lines = assistant."""
    messages = [{"role": "system", "content": _system(p, seed)}] + dialogue
    return await chat_text(messages, temperature=0.9)


JUDGE_SCHEMA_HINT = (
    'Return JSON: {"converted": bool, "disqualified": bool, "walked": bool, '
    '"price_objection_raised": bool, "price_objection_resolved": bool, '
    '"realism": number_0_to_1, "note": string}'
)


async def judge_outcome(p: Prospect, transcript: list[dict]) -> dict:
    convo = "\n".join(f"{t['role']}: {t['content']}" for t in transcript)
    msg = await chat(
        [
            {"role": "system", "content":
                "You are an impartial sales-call evaluator. Given a transcript between an AI "
                "advisor and a prospect, judge what actually happened. Be strict: 'converted' "
                "means the prospect genuinely agreed to a concrete next step (consult/trial/"
                "session), not vague politeness. " + JUDGE_SCHEMA_HINT},
            {"role": "user", "content": f"Persona: {p.label} ({p.fit}).\n\nTranscript:\n{convo}"},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(msg.get("content") or "{}")
    except json.JSONDecodeError:
        return {"converted": False, "disqualified": False, "walked": True,
                "price_objection_raised": False, "price_objection_resolved": False,
                "realism": 0.0, "note": "judge parse error"}
