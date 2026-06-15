# Failure-Mode Report

An honest account of how Ada can fail, what we did about it, and what's still open. The PRD's
rubric is explicit that a strong submission *exposes* weaknesses rather than hiding them, so
this is written to be used, not to reassure.

## Conversation / voice

- **Latency spikes.** The Realtime socket is usually snappy, but a slow tool call (KB embedding
  round-trip) can stall a turn. *Mitigation:* KB lookups are small and cached-friendly; the
  model is told it may acknowledge ("let me check that") before the result returns. *Open:* no
  hard latency budget enforced yet.
- **Transcription errors on the phone.** G.711 at 8 kHz is lower fidelity than the web's 24 kHz
  PCM; names and numbers can mis-transcribe. *Mitigation:* PII redaction is regex-based and
  tolerant; Ada confirms key facts back. *Open:* no explicit "spell that back" confirmation step.
- **Barge-in races.** If the caller interrupts exactly as a response starts, a few hundred ms of
  Ada's audio can still play before the cancel lands. *Mitigation:* we send `response.cancel` and
  flush the client/Twilio buffer on `speech_started`. *Open:* rare clipped overlap remains.

## Knowledge & grounding

- **Retrieval miss → over-escalation.** If a real question sits just under the relevance floor,
  Ada says she'll confirm and escalates instead of answering. This is the *safe* failure
  (no hallucination) but can feel evasive. *Tuning knob:* `kb._FLOOR` (currently 0.28).
- **Stale KB.** Grounding is only as good as the documents. The seeded content is synthetic demo
  policy; production must load Nerdy's real, dated policy/pricing docs.

## Decisioning

- **Premature pivot.** `ready_to_close` fires when all *required* fields are gathered; a prospect
  who answered tersely can be pushed to close early. *Mitigation:* the close is phrased as a
  low-friction next step, not a hard ask. *Open:* no "readiness to buy" signal beyond field
  coverage.
- **Under-escalation on price concessions.** Ada is told to escalate real concessions, but a
  clever prospect can still pull a small discount narrative. The improvement loop specifically
  targets this dimension.

## The improvement loop itself (meta-failure modes)

- **Judge bias.** Conversion is scored by an LLM judge. A lenient judge inflates close rate.
  *Mitigation:* the judge prompt is strict ("vague politeness is not conversion"), runs at
  temperature 0, and reports a `realism` score we watch. *Open:* no human-labeled calibration set
  yet.
- **Obedient-prospect trap (the rubric's headline risk).** If synthetic prospects always agree,
  every variant "wins." *Mitigation:* the prospect library is adversarial by construction —
  budget-skeptic, fence-sitter, comparison-shopper, and an out-of-fit disqualifier who *should*
  be turned away. Close rate excludes correct disqualifications so the agent can't farm easy wins.
- **Overfitting to synthetic prospects.** A variant can win against simulated leads and flop with
  real humans. *Mitigation:* the loop is the *signal generator*, not the final word — promotions
  above a large delta are flagged for human review, not auto-shipped. The real test is a human on
  the line, which the web/phone channels make easy.

## Operational

- **Single SQLite file.** Fine for a demo and a single service; concurrent heavy write load would
  need Postgres. *Open by design.*
- **No auth on the dashboard.** The observability API is open in the demo. Add auth before any
  real PII flows.
