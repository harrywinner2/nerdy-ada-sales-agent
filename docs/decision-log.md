# Decision Log

Two things share this name in the project, and both matter to the PRD.

## 1. The per-call decision log (a product feature)

Every call produces a stream of **decision records** so a reviewer can see *why* Ada did what
she did, not just what was said. Each record is `{turn_index, action, candidates, confidence,
rationale, ts}` and is visible on the Call detail screen as a timeline.

Actions:

| Action | When it's logged | Example rationale |
|---|---|---|
| `ask` | Ada moves discovery forward | `prioritized discovery: student_grade` |
| `answer` | Ada answers from the knowledge base | `grounded:true cites:Tutoring Plans & Pricing` |
| `pivot_close` | All required fields gathered, or outcome is a booking | `all required fields gathered` |
| `escalate` | Low-confidence turn / high-stakes moment | `high: caller demanding a score guarantee` |
| `disqualify` | Prospect is out of fit and let go politely | `outcome=disqualified` |

Where they come from: discovery decisions are computed from the **playbook** state each agent
turn (`CallSession.log_ask`), and the rest are emitted by the **server-side tools**
(`CallSession.execute_tool`) — a knowledge lookup logs an `answer` with its citations and
relevance score, `set_outcome` logs a `pivot_close`/`disqualify`, `escalate` logs an
`escalate`. Because tools are executed identically on the voice path and the text self-play
path, the decision log looks the same for a real phone call and a simulated one. This is what
the PRD means by "decisions … accessible through a dashboard, not buried in logs."

The `confidence` is a coarse, honest signal (playbook certainty / KB top-score), not a
fabricated precision. `candidates` shows the other questions Ada *considered* asking, so you can
audit prioritization.

## 2. Key engineering decisions (how we built it)

The running narrative is in `BUILD_LOG.md`. The decisions that shaped the architecture:

- **OpenAI Realtime (speech-to-speech), not STT→LLM→TTS.** One socket, server-side VAD, native
  barge-in, and native G.711 for the phone bridge. Fewer hops = lower latency and less to break.
- **One FastAPI service serving the React build.** The voice relay needs a persistent
  WebSocket, which rules out serverless. One service is simplest to reason about and deploy.
- **Railway over Vercel/Cloudflare.** Railway runs long-lived WebSocket processes natively;
  Vercel is serverless and Cloudflare would need Durable Objects.
- **SQLite as both memory and observability store.** Zero-ops, file-backed, and the schema ports
  to Postgres unchanged if Nerdy scales.
- **Text-mode self-play for the loop.** Running the *same* agent logic over text (not audio)
  makes experiments cheap enough to run many calls; improvements transfer because the persona,
  tools, grounding, and playbook are shared code.
- **Improve by prompt/playbook variants, not fine-tuning.** The PRD lists fine-tuning as
  optional; a variant loop is the part that has to *run*, and it changes behavior with zero
  redeploys (variants live in the DB and are swapped per session).
- **Honest KPIs.** Close rate excludes correctly-disqualified out-of-fit prospects, so the agent
  can't game the metric by refusing to let bad-fit leads go.
