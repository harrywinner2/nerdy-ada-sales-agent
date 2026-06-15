# Limitations Memo

What Ada is not, and where the edges are. Read this before trusting any number or shipping to
real customers.

## Scope
- **English only.** No multilingual handling in this build.
- **Tutoring sales discovery-to-close**, stopping at a booked consult or trial. No payment
  capture, no CRM write-back, no contract generation.
- **Demo knowledge base.** The seeded policy/pricing/competitive content is *synthetic* and
  modeled on plausible Nerdy/Varsity Tutors answers. It is not authoritative. Replace it with
  Nerdy's real, dated documents before any customer-facing use — the grounding is only as correct
  as its sources.

## Data & privacy
- PII is substituted at write time (names/phones/emails → stable tokens) so stored transcripts
  are PII-free, but the **redactor is heuristic** (regex). It will miss unusual name formats and
  may over-redact capitalized phrases. It is a safety net, not a compliance guarantee.
- The dashboard and observability API have **no authentication** in the demo. Do not expose real
  customer data without adding access control.
- SQLite is single-file; there is no encryption at rest configured.

## Voice
- Phone audio is 8 kHz μ-law — lower fidelity than the web channel; expect more transcription
  error on names and numbers.
- Barge-in is good but not perfect; a sub-second overlap can occur on exact-timing interrupts.
- No call recording is stored (only transcripts), by design.

## The KPIs and the loop
- **Conversion is judged by an LLM**, not by a real booking system. The judge is strict and runs
  at temperature 0, but it is still a model evaluating a model. Treat close-rate movements as a
  strong *signal*, validated by putting a human on the line — not as audited revenue.
- Experiment sample sizes in a quick run are **small** (a handful of calls per arm). Deltas are
  directional; widen seeds/prospects for statistical confidence before promoting high-stakes
  changes. Large promotions are flagged for human review rather than auto-shipped.
- Results can **overfit** to the synthetic prospects. The prospects are adversarial by design,
  but they are not real customers.

## Operational
- One process, one SQLite file: great for a demo and a single region, not for high concurrency.
  The schema ports to Postgres; the relay scales horizontally only with a shared DB and sticky
  WebSockets.
- Costs scale with usage: Realtime audio minutes (live calls) and text tokens (each experiment
  runs many simulated calls). A large experiment is the most expensive single action.
- Keys used for this build should be **rotated** after the engagement.
