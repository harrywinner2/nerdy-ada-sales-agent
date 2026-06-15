# Nerdy — Autonomous AI Sales Agent (Expanded PRD)

> Source of truth: the original PRD (`tmp3.pdf`) + the pasted brief. This document adds the
> engineering detail needed to actually ship it: architecture, data model, the runtime AI
> surface, the recursive-improvement loop, and acceptance criteria. Where the PRD left a
> choice open, the decision and its rationale are recorded inline and in `BUILD_LOG.md`.

Codename: **Ada** — the Nerdy AI Sales Agent. (A consistent persona is a hard requirement;
naming her up front keeps voice, copy, and transcripts coherent.)

---

## 1. What we're building (one paragraph)

A voice AI sales agent that can hold a complete **discovery-to-close** tutoring sales call —
over the **web** (browser mic, for instant testing) and over a **real phone line** (Twilio, for
end-to-end realism). She gathers required and leading information, remembers prior calls,
answers policy/objection/competitive questions **only** from a grounded knowledge base, and
decides turn-by-turn what to ask, when to pivot to close, and when to escalate. Every call is
fully observable (transcript + decision log + outcome + version tag) through a dashboard. A
**recursive improvement loop** pits the agent against honest, adversarial **synthetic
prospects**, generates variants of a chosen dimension, runs controlled experiments, and
promotes or retires variants on measured KPI movement — with before/after evidence.

This is **end-to-end functional**, not a mockup (per the PRD deliverables). The mockup in
`ui/mockup.html` is an internal design artifact only.

---

## 2. Architecture & rationale

```
                         ┌─────────────────────────────────────────────┐
   Browser (mic/spkr) ───┤ /ws/web      (PCM16 duplex)                  │
                         │                                              │
   Phone  ──Twilio──────►│ /twilio/voice (TwiML) + /ws/twilio (μ-law)   │
                         │            FastAPI relay (Python)            │
                         │   ┌──────────────────────────────────────┐  │
                         │   │ Session: persona + active VARIANT     │  │
                         │   │  ├─ OpenAI Realtime API (speech↔speech)│ │◄── gpt-realtime
                         │   │  ├─ tools: kb_lookup, save_field,      │  │
                         │   │  │         escalate, set_outcome       │  │
                         │   │  ├─ Playbook engine (next-question)    │  │
                         │   │  └─ Decision logger                    │  │
                         │   └──────────────────────────────────────┘  │
                         │        │              │            │         │
                         │   Knowledge Base   Memory       KPIs         │
                         │   (embeddings)    (SQLite)    (computed)      │
                         └────────┼──────────────┼────────────┼─────────┘
                                  │              │            │
   React dashboard ◄─── REST /api │  ◄───────────┘            │
   (transcripts, decisions,       └─ Recursive loop: simulator + experiments
    KPIs, experiments)                 (text self-play, gpt-4.1-mini)
```

**Why these choices**

- **OpenAI Realtime API (speech-to-speech) for the voice core.** A single server-side
  WebSocket carries audio in and audio out with built-in VAD, turn detection, and **barge-in**.
  This is the lowest-latency path to "natural turn-taking" and avoids stitching separate STT +
  LLM + TTS hops (each adds latency and failure surface). It also speaks **G.711 μ-law**
  natively, so the Twilio phone bridge is a near pass-through. Matches the all-OpenAI provider
  posture; sidesteps the Deepgram network block.
- **FastAPI relay (Python).** PRD-required language/framework. The relay is the trust boundary:
  the OpenAI key never reaches the browser; tools (KB, memory, escalation) run server-side; we
  inject the persona + the *active experiment variant* per session and log every decision.
- **Text-mode agent for self-play.** The exact same prompt/tool logic runs against
  `gpt-4.1-mini` in text for the recursive loop. Self-play over **text** (not audio) makes
  experiments fast and cheap enough to run hundreds of calls, while production stays voice.
- **SQLite for memory + observability.** Zero-ops, file-backed, perfect for a single Railway
  service and a demo; the schema is portable to Postgres if Nerdy scales. PII is substituted at
  write time (see §6).
- **Embedded vector KB.** Docs embedded with `text-embedding-3-small`; cosine top-k retrieval;
  the model is instructed to answer **only** from retrieved context → grounded, no hallucinated
  policy/pricing.
- **React dashboard, served by FastAPI.** One deployable service on **Railway** (which runs
  persistent WebSockets natively — the deciding factor over Vercel/CF Workers).

---

## 3. Screen / route inventory (dashboard)

| Route | Screen | Purpose |
|---|---|---|
| `/` | **Live Call** | Talk to Ada in-browser (mic), watch live transcript + decisions + waveform. The "test it yourself" surface. |
| `/calls` | **Calls** | List of all calls (web + phone + simulated) with outcome, version tag, KPIs. |
| `/calls/:id` | **Call detail** | Full transcript, decision timeline (next-Q / pivot / escalate + confidence), lead profile gathered, outcome. |
| `/knowledge` | **Knowledge base** | Browse/search grounded KB docs; see what Ada can cite. |
| `/experiments` | **Recursive improvement** | Variants of a chosen dimension, A/B results vs baseline, promote/retire, **before/after KPI charts**. |
| `/personas` | **Synthetic prospects** | The adversarial prospect library used for self-play (hesitant, price-pusher, disqualifier…). |
| `/overview` | **KPIs** | Top-line KPI dashboard across versions. |

Every nav item is real and wired (skill rule).

---

## 4. Runtime AI surface

**Persona (Ada).** Warm, concise, consultative Nerdy/Varsity Tutors advisor. Never robotic,
never a script-reader. System prompt = persona + current playbook state + active variant text +
grounding rules + tool instructions + loaded prior-call memory.

**Tools exposed to the model (function calling, server-executed):**
- `lookup_knowledge(query)` → grounded answer chunks from KB (policy/objection/competitive/pricing).
- `save_lead_field(field, value)` → persist a discovered field (grade, subject, goal, timeline, budget…).
- `set_outcome(outcome, notes)` → mark booked_consult / trial / not_now / disqualified.
- `escalate(reason, severity)` → flag a low-confidence turn or high-stakes moment (e.g. pricing concession) for a human.

**Decisioning.** The **playbook engine** maintains the prioritized list of required + leading
questions, applies *skip-when-already-known*, and surfaces the top candidates to the model each
turn. After each user turn we log a **decision record**: chosen action (`ask` / `pivot_close` /
`escalate` / `answer`), the candidate questions considered, and a confidence score. This is what
the PRD means by "decisions made … accessible through a dashboard, not buried in logs."

**Memory (cross-call).** On call start we look up the lead by phone/email/id, load their profile
and a short summary of prior calls into the session ("Last time you mentioned your daughter is
in 9th-grade geometry…"). New fields persist back.

**Grounding rule.** For any policy/price/competitive claim, Ada must call `lookup_knowledge`
and answer only from returned context; if the KB has no answer, she says so and may `escalate`
rather than invent.

---

## 5. Recursive improvement loop (the part the rubric weighs most)

**Chosen single dimension to prove the pattern:** the **price-objection rebuttal** (one of the
PRD's suggested dimensions). It's high-leverage, easy to vary, and directly tied to a KPI.

**Honest synthetic prospects.** A library of LLM personas that *do not* simply agree: the
*Budget-Skeptic* pushes hard on price, the *Fence-Sitter* hesitates and stalls, the
*Disqualifier* turns out to be out-of-ICP (wrong grade/subject) and should be let go, the
*Comparison-Shopper* name-drops competitors. Each has hidden goals and walk-away conditions, so
a win has to be earned. (Directly answers the rubric's "obedient leads" failure mode.)

**Loop mechanics:**
1. **Baseline.** Run the current rebuttal across the prospect mix → record KPIs.
2. **Variant generation.** An LLM proposes N alternative rebuttals (different framing: value,
   ROI, risk-reversal/guarantee, social proof).
3. **Controlled experiment.** Each variant runs the *same* prospect seeds (paired/controlled).
4. **Scoring & decision.** Compare to baseline on the target KPI; **promote** the winner,
   **retire** losers. Low-stakes → auto-promote; large swings → escalate for human approval.
5. **Evidence.** Before/after KPI numbers + sample transcripts persisted and shown on
   `/experiments`.

**KPIs tracked:**
- **Close rate** — % calls ending in booked consult / trial (primary target KPI).
- **Discovery completeness** — % of required fields gathered.
- **Objection-resolution rate** — objections raised that were resolved (not deflected).
- **Avg turns to outcome** — efficiency.
- **Escalation rate** — share of turns/calls escalated.
- **Groundedness** — share of factual claims backed by a KB citation.

Every call (real or simulated) is tagged with the **agent version** (persona + active variant
hash) so KPIs attribute correctly.

---

## 6. Data model (SQLite)

- `leads` — id, name*, phone*, email*, profile_json (grade, subjects, goals, budget, timeline), created_at. *(PII fields substituted: stored as salted tokens + display alias; raw PII never persisted.)*
- `calls` — id, lead_id, channel (web/phone/sim), version_tag, outcome, started_at, ended_at, kpis_json.
- `turns` — id, call_id, role (agent/prospect), text, audio_ms, ts.
- `decisions` — id, call_id, turn_index, action, candidates_json, confidence, rationale.
- `escalations` — id, call_id, reason, severity, ts.
- `kb_docs` — id, title, category, content, embedding (blob).
- `variants` — id, dimension, label, text, status (baseline/candidate/promoted/retired), parent_id.
- `experiments` — id, dimension, created_at, summary_json.
- `experiment_runs` — id, experiment_id, variant_id, prospect_persona, kpis_json, transcript_json.

**PII protection.** Names/phones/emails passing through transcripts are detected and replaced
with stable tokens (`<NAME_1>`, `<PHONE_1>`) before storage; a per-call alias map lives in
memory only for the call's duration. The transcript DB is therefore PII-substituted by
construction (PRD requirement).

---

## 7. Acceptance criteria

**Conversation**
- [ ] Two-way live voice on web with barge-in; agent audibly stops when interrupted.
- [ ] Real inbound phone call (Twilio) reaches Ada and back (when Twilio creds present).
- [ ] Handles a lead with full / partial / no prior info; loads prior-call memory when present.
- [ ] Persona stays consistent across a full call.

**Discovery & knowledge**
- [ ] Asks prioritized required + leading questions; skips already-known fields.
- [ ] Policy/price/competitive answers are grounded in KB (citation present); refuses/escalates when unknown.

**Decisioning & observability**
- [ ] Each turn produces a decision record (action + candidates + confidence).
- [ ] Dashboard shows transcript + decision timeline + outcome + version tag per call.
- [ ] KPI overview renders across versions.

**Recursive improvement**
- [ ] Synthetic prospects demonstrably push back / disqualify (not obedient).
- [ ] One full loop runs: baseline → variants → controlled experiment → promote/retire.
- [ ] Before/after evidence on a real KPI is visible on `/experiments`.

**Quality / docs**
- [ ] Failure-mode report, recursive-improvement description, decision-log explanation, research
      notes, limitations memo.
- [ ] Public repo, live Railway URL, verified core flows.

---

## 8. Out of scope (delete so we don't build phantoms)
- Real payment capture / CRM write-back (we stop at "booked consult / trial").
- Multi-language (English only for the demo).
- Fine-tuning the base model (the PRD lists it as optional; we improve via prompt/playbook
  variants, which is the loop that's required to *run*).
- WhatsApp channel (web + phone chosen).
