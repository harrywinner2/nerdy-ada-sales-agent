# Research Notes

Working notes from building Ada — what we tried, what we chose, and why. Kept candid.

## Voice transport
- Compared **STT→LLM→TTS** (cascade) against **speech-to-speech** (OpenAI Realtime). The cascade
  is more modular (swap any vendor) but adds 2–3 network hops of latency and a lot of glue for
  turn detection and barge-in. For "natural turn-taking," the single Realtime socket won. The
  cascade remains the fallback if a client mandates a specific STT/TTS vendor.
- The Realtime API speaks **G.711 μ-law** natively, which collapses the Twilio bridge to almost a
  pass-through (no transcode). This single fact made the phone channel cheap to add.
- Voice choice: `marin` — one of the newer, warmer Realtime voices — reads as a credible advisor.
  `cedar` is the male alternative if persona testing wants it.

## Grounding
- Embeddings with `text-embedding-3-small` + cosine similarity over a dozen docs is more than
  enough at this scale; a heavier vector DB would be premature. We store vectors as packed float
  blobs in SQLite and compute similarity in NumPy.
- The **relevance floor** matters more than k. Too low and Ada answers off-topic questions from
  loosely-related docs; too high and she over-escalates. 0.28 was a reasonable balance on the
  seeded set; it should be re-tuned per real corpus.

## Decisioning
- We deliberately kept the playbook **deterministic** (a ranked field list with skip-when-known)
  rather than asking the model to plan discovery from scratch each turn. The model is great at
  *phrasing* and *reading the room*; it's less reliable at consistently covering a checklist. So
  the playbook owns coverage, the model owns delivery. This split also makes the discovery KPI
  trivially measurable.

## Synthetic prospects
- First draft prospects were too cooperative — they converted regardless of the rebuttal, which
  made every variant look good. Rewriting them with **hidden goals and walk-away conditions**
  (and adding an out-of-fit disqualifier) restored discriminating power. The judge's `realism`
  score is the canary: if it drops, the prospects have gone robotic.
- Higher temperature (0.9) on the prospect, low temperature (0.0) on the judge. The prospect
  should be varied and human; the evaluator should be boring and consistent.

## The loop
- Chose **price-objection rebuttal** as the first dimension because it's high-leverage, easy to
  vary along clear axes (value/ROI, risk-reversal, social proof), and maps directly to close
  rate. The framework is dimension-agnostic — `persona.DIMENSION` and `variants.dimension` are
  the only coupling — so opening-question phrasing or sequencing rules are next.
- **Paired seeds**: each variant faces the same prospect seeds, so differences are about the
  rebuttal, not luck of the draw.

## Things deferred (with reasons)
- **Fine-tuning** — the loop that must *run* is variant-based; fine-tuning is a later lever once
  there's a labeled corpus.
- **RAG over full sales books** — indexing methodology guides would enrich answers, but grounded
  policy/pricing is the higher-value, lower-risk starting corpus.
- **A human-labeled calibration set** for the judge — the single most useful next investment to
  trust the KPIs.
