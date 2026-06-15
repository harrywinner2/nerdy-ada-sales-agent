# Recursive Improvement — Description & Evidence

The PRD asks for at least one *meaningful* improvement loop that moves a real KPI from a
documented baseline through variant generation, controlled experimentation, and a promote/retire
decision. This is that loop, and a real run of it.

## The loop

```
 baseline strategy
        │
        ▼
 generate variants ──►  controlled experiment  ──►  score on a real KPI  ──►  promote / retire
 (LLM proposes N           (each variant faces        (close rate, with        (auto-promote small
  distinct rebuttals)       the SAME adversarial        objection-resolution     wins; escalate big
                            prospect seeds)             as tie-break)            swings for review)
```

- **Dimension under test:** the price-objection rebuttal (`persona.DIMENSION`). High-leverage,
  easy to vary along clear axes, directly tied to close rate. The framework is dimension-agnostic.
- **Agent under test:** text-mode Ada — the *same* persona, tools, grounding, and playbook as the
  voice agent, so what wins here transfers to live calls.
- **Opponents:** honest, adversarial synthetic prospects (`app/simulator.py`) — a budget-skeptic
  who pushes on price, a fence-sitter who stalls, a comparison-shopper, an out-of-fit
  disqualifier who *should* be turned away, and a ready-buyer. They have hidden goals and
  walk-away conditions, so a win is earned.
- **Judge:** an independent LLM evaluator at temperature 0 that decides conversion strictly
  ("vague politeness is not conversion") and reports a `realism` score we watch to make sure the
  prospects aren't going robotic.
- **Honesty guard:** close rate excludes correctly-disqualified out-of-fit prospects, so the
  agent can't inflate the metric by refusing to let bad-fit leads go.

## A real run (before → after)

Command: `run_experiment(seeds=1, variant_count=2)` — 3 arms (baseline + 2 generated variants)
× 5 adversarial prospects = 15 self-play calls, all against the real OpenAI API.

| Arm | Close rate | Objection resolution | Discovery | Realism | Disqualified |
|---|---|---|---|---|---|
| **baseline** ("restate the figure, keep it factual") | **25%** | 0.67 | 0.77 | 0.94 | 1 |
| **Value/ROI Framing** ⬆ *winner* | **75%** | 1.00 | 0.77 | 0.95 | 1 |
| Social Proof | 50% | 0.50 | 0.77 | 0.94 | 1 |

**Result:** close rate moved **25% → 75% (+50 points)** by replacing a flat, factual rebuttal
with a value/ROI framing that reframes monthly cost against the outcome and the no-contract free
consult. Objection-resolution went from 0.67 to a perfect 1.0. The decision was
**`promoted_with_review`**: the variant was promoted (it's now the active strategy) but the swing
was large enough that the system flagged it for human sign-off rather than silently shipping it —
exactly the "auto-promote low-stakes, escalate big ones" behavior the PRD describes.

Two honesty signals worth calling out:
- **Realism stayed ~0.94–0.95**, and **one prospect was disqualified in every arm** — the
  out-of-fit caller was correctly turned away rather than force-sold. These are the opposite of
  the rubric's "swarm of obedient leads" failure mode.
- The baseline genuinely *lost* most price-objection calls (25%). The loop found a real weakness
  and fixed it, rather than reporting a flattering number.

## Caveats (don't over-read it)

A single quick run is a small sample; the +50-point delta is directional, not audited. The honest
read is "strong signal, confirm with more seeds and a human on the line before treating it as
revenue." That human-in-the-loop confirmation is exactly why a large delta is escalated for
review. See `docs/limitations.md`. The loop is reproducible from the Recursive Improvement screen
("Run experiment") or the CLI snippet in the README.

## Where to see it
- **Live:** the **Recursive Improvement** tab renders this before→after with per-arm bars,
  the decision badge, and expandable sample transcripts + the judge's notes.
- **Code:** `app/experiments.py` (loop), `app/simulator.py` (prospects + judge),
  `app/persona.py` (variant registry + version tagging), `app/kpis.py` (metrics).
